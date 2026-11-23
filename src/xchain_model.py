#!/usr/bin/env python3
"""xchain_model.py — pure-stdlib mirror of the pinned postfiatd XChain rules.

Every function mirrors one named routine in the pinned source
(postfiatorg/postfiatd @ 0085a1ff885d6a446369cf73a4430f75af22be55,
src/xrpld/app/tx/detail/XChainBridge.cpp and
src/libxrpl/protocol/XChainAttestations.cpp). The mirror is structural:
it reproduces the decision rules (weight sums, quorum comparison,
replace-on-replay, field validation) on synthetic lab data. It does NOT
reproduce cryptography: attestation signature verification calls
ripple::verify (Ed25519), which is not in the Python standard library,
so the model takes the signature-verification outcome as an input
(`signature_valid`) and marks that boundary explicitly.

Amounts are integer drops (XRP-native units). Account IDs and public keys
are opaque strings; in the model a public key is represented by the
account ID it derives to, because key derivation is outside the model.
"""

# TER-style result codes used by the pinned code (subset, XChain only).
TES_SUCCESS = "tesSUCCESS"
TEM_DISABLED = "temDISABLED"
TEM_MALFORMED = "temMALFORMED"
TEM_BAD_AMOUNT = "temBAD_AMOUNT"
TEM_XCHAIN_EQUAL_DOOR_ACCOUNTS = "temXCHAIN_EQUAL_DOOR_ACCOUNTS"
TEM_XCHAIN_BRIDGE_NONDOOR_OWNER = "temXCHAIN_BRIDGE_NONDOOR_OWNER"
TEM_XCHAIN_BRIDGE_BAD_ISSUES = "temXCHAIN_BRIDGE_BAD_ISSUES"
TEM_XCHAIN_BRIDGE_BAD_REWARD_AMOUNT = "temXCHAIN_BRIDGE_BAD_REWARD_AMOUNT"
TEM_XCHAIN_BRIDGE_BAD_MIN_ACCOUNT_CREATE_AMOUNT = (
    "temXCHAIN_BRIDGE_BAD_MIN_ACCOUNT_CREATE_AMOUNT")
TEM_XCHAIN_BAD_PROOF = "temXCHAIN_BAD_PROOF"
TEC_NO_PERMISSION = "tecNO_PERMISSION"
TEC_XCHAIN_BAD_PUBLIC_KEY_ACCOUNT_PAIR = "tecXCHAIN_BAD_PUBLIC_KEY_ACCOUNT_PAIR"
TEC_XCHAIN_CLAIM_NO_QUORUM = "tecXCHAIN_CLAIM_NO_QUORUM"
TEC_INTERNAL = "tecINTERNAL"

# The root account the pinned code derives for an XRP issuing door:
# generateKeyPair(secp256k1, generateSeed("masterpassphrase")).
# XChainBridge.cpp preflight, and xrpl.org XChainCreateBridge docs:
# for an XRP-XRP bridge the issuing door must be the genesis account.
MASTERPASSPHRASE_ROOT = "r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59"

UINT32_MAX = 0xFFFFFFFF


class Attestation:
    """One witness attestation (synthetic lab data).

    Mirrors Attestations::AttestationClaim /
    Attestations::AttestationCreateAccount in
    src/libxrpl/protocol/XChainAttestations.cpp: the fields the pinned
    code matches on are sending account, sending amount, chain direction,
    claim id / create count, destination, reward account, signer account
    and public key. `signature_valid` stands in for
    AttestationBase::verify (Ed25519), which this model cannot run.
    """

    def __init__(self, signer_account, public_key_account, sending_account,
                 sending_amount_drops, was_locking_chain_send, claim_id,
                 destination, reward_account, signature_valid=True,
                 public_key_type="ed25519", issue="XRP"):
        self.signer_account = signer_account
        self.public_key_account = public_key_account
        self.sending_account = sending_account
        self.sending_amount_drops = sending_amount_drops
        self.was_locking_chain_send = was_locking_chain_send
        self.claim_id = claim_id
        self.destination = destination
        self.reward_account = reward_account
        self.signature_valid = signature_valid
        self.public_key_type = public_key_type
        self.issue = issue

    @property
    def key_account(self):
        # The pinned code keys attestations by attestationSignerAccount.
        return self.signer_account


class AttestationSet:
    """The accumulated attestations on one claim id.

    Mirrors XChainAttestationsBase<TAttestation>: one entry per signer
    account, keyed by signer.
    """

    def __init__(self):
        self.attestations = []

    def __len__(self):
        return len(self.attestations)

    def add_or_replace(self, att):
        """Mirror of onNewAttestations' insert loop: an attestation from
        a signer that already attested REPLACES the old one; it never
        adds a second entry for the same signer. Returns True if the
        collection changed."""
        for i, a in enumerate(self.attestations):
            if a.key_account == att.key_account:
                self.attestations[i] = att
                return True
        self.attestations.append(att)
        return True

    def erase_non_signers(self, signers):
        """Mirror of claimHelper's erase_if: drop attestations whose
        signer is not in the current signers list (or whose key no
        longer checks out)."""
        before = len(self.attestations)
        self.attestations = [a for a in self.attestations
                             if a.key_account in signers]
        return before - len(self.attestations)


def check_attestation_public_key(signers, signer_account, public_key_account,
                                 account_exists, master_disabled,
                                 regular_key_account):
    """Mirror of checkAttestationPublicKey (XChainBridge.cpp ~111-175).

    signers: dict account -> weight (the door account's SignerList).
    public_key_account: the account the attestation's public key derives
    to (model input standing in for calcAccountID(pk)).
    account_exists / master_disabled / regular_key_account describe the
    signer's account on the ledger; pass account_exists=False when the
    account does not exist.
    """
    if signer_account not in signers:
        return TEC_NO_PERMISSION
    if account_exists:
        if public_key_account == signer_account:
            # master key
            if master_disabled:
                return TEC_XCHAIN_BAD_PUBLIC_KEY_ACCOUNT_PAIR
        else:
            # regular key: must equal the account's RegularKey
            if regular_key_account != public_key_account:
                return TEC_XCHAIN_BAD_PUBLIC_KEY_ACCOUNT_PAIR
    else:
        # account does not exist: key must derive to the signer account
        if public_key_account != signer_account:
            return TEC_XCHAIN_BAD_PUBLIC_KEY_ACCOUNT_PAIR
    return TES_SUCCESS


def claim_helper(att_set, to_match, check_dst, quorum, signers):
    """Mirror of claimHelper (XChainBridge.cpp ~189-242).

    to_match: dict with sending_amount_drops, was_locking_chain_send,
    destination (None = ignore destination).
    check_dst: "check" (add-attestation path) or "ignore" (claim path).
    Returns (reward_accounts, None) on quorum, or (None, TER) with
    tecXCHAIN_CLAIM_NO_QUORUM when weight < quorum.
    """
    att_set.erase_non_signers(signers)
    weight = 0
    reward_accounts = []
    for a in att_set.attestations:
        if a.sending_amount_drops != to_match["sending_amount_drops"]:
            continue
        if a.was_locking_chain_send != to_match["was_locking_chain_send"]:
            continue
        if check_dst == "check":
            if a.destination != to_match.get("destination"):
                continue
        if a.key_account not in signers:
            continue
        weight += signers[a.key_account]
        reward_accounts.append(a.reward_account)
    if weight >= quorum:
        return reward_accounts, None
    return None, TEC_XCHAIN_CLAIM_NO_QUORUM


def on_new_attestations(att_set, new_atts, to_match, quorum, signers):
    """Mirror of onNewAttestations (XChainBridge.cpp ~282-350).

    Adds/replaces each new attestation, then runs claimHelper with
    CheckDst::check. Returns (reward_accounts_or_None, changed).
    """
    changed = False
    for att in new_atts:
        changed = att_set.add_or_replace(att) or changed
    rewards, err = claim_helper(att_set, to_match, "check", quorum, signers)
    if err is not None:
        return None, changed
    return rewards, changed


def on_claim(att_set, sending_amount_drops, was_locking_chain_send,
             quorum, signers):
    """Mirror of onClaim (XChainBridge.cpp ~352-366): claimHelper with
    CheckDst::ignore — the destination is not checked on the claim
    path."""
    to_match = {"sending_amount_drops": sending_amount_drops,
                "was_locking_chain_send": was_locking_chain_send,
                "destination": None}
    return claim_helper(att_set, to_match, "ignore", quorum, signers)


def validate_create_bridge(submitter, locking_door, issuing_door,
                           locking_is_xrp, issuing_is_xrp,
                           locking_issue_account, issuing_issue_account,
                           signature_reward_is_xrp, signature_reward_drops,
                           min_account_create_drops,
                           min_account_create_is_xrp=True,
                           root_account=MASTERPASSPHRASE_ROOT):
    """Mirror of XChainCreateBridge::preflight (XChainBridge.cpp
    1374-1447). Returns a TER string; tesSUCCESS when the bridge spec
    passes every preflight rule. min_account_create_drops is None when
    the field is absent."""
    if locking_door == issuing_door:
        return TEM_XCHAIN_EQUAL_DOOR_ACCOUNTS
    if submitter != locking_door and submitter != issuing_door:
        return TEM_XCHAIN_BRIDGE_NONDOOR_OWNER
    if locking_is_xrp != issuing_is_xrp:
        return TEM_XCHAIN_BRIDGE_BAD_ISSUES
    if not signature_reward_is_xrp or signature_reward_drops < 0:
        return TEM_XCHAIN_BRIDGE_BAD_REWARD_AMOUNT
    if min_account_create_drops is not None:
        if (not min_account_create_is_xrp or min_account_create_drops <= 0
                or not locking_is_xrp or not issuing_is_xrp):
            return TEM_XCHAIN_BRIDGE_BAD_MIN_ACCOUNT_CREATE_AMOUNT
    if issuing_is_xrp:
        # Issuing account must be the root account for XRP.
        if issuing_door != root_account:
            return TEM_XCHAIN_BRIDGE_BAD_ISSUES
    else:
        # Issuing account must be the issuer for non-XRP.
        if issuing_door != issuing_issue_account:
            return TEM_XCHAIN_BRIDGE_BAD_ISSUES
    if locking_door == locking_issue_account:
        return TEM_XCHAIN_BRIDGE_BAD_ISSUES
    return TES_SUCCESS


def validate_attestation_preflight(att, expected_issue):
    """Mirror of attestationpreflight (XChainBridge.cpp 1215-1241).

    expected_issue: the bridge's issue on the sending chain
    ("XRP" for a native-asset bridge, else "CODE/issuer").
    Returns tesSUCCESS or a tem code. The signature check
    (AttestationBase::verify) is represented by att.signature_valid;
    real Ed25519 verification is outside this model.
    """
    if att.public_key_type not in ("ed25519", "secp256k1"):
        return TEM_MALFORMED
    if not att.signature_valid:
        return TEM_XCHAIN_BAD_PROOF
    if att.sending_amount_drops <= 0:
        return TEM_XCHAIN_BAD_PROOF
    if att.issue != expected_issue:
        return TEM_XCHAIN_BAD_PROOF
    return TES_SUCCESS


def create_claim_id(current_counter):
    """Mirror of XChainCreateClaimID::doApply (XChainBridge.cpp
    2035-2098): the claim id is the bridge counter + 1; a wrap to 0 is
    an internal error. Returns (next_id, None) or (None, TER)."""
    nxt = current_counter + 1
    if nxt == 0 or nxt > UINT32_MAX:
        return None, TEC_INTERNAL
    return nxt, None
