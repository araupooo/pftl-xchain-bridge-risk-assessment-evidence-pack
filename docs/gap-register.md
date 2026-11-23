# Gap Register

| ID | Gap | Why it is open | What would close it |
| --- | --- | --- | --- |
| G-01 | Attestation signature verification (Ed25519) | No Ed25519 in the Python standard library; the model takes the signature outcome as an input | A verification run with an Ed25519 implementation (e.g. libsodium) against real attestation payloads |
| G-02 | Whether any bridge ever existed under an unknown door account | No RPC lists bridges; the probes cover the only door pair the pinned code makes identifiable (genesis + masterpassphrase root over XRP) | A full ledger scan for Bridge objects, or operator disclosure of any bridge ever created |
| G-03 | Live XChain behaviour end to end | XChainBridge is disabled, so no XChain transaction can execute on the live network | The amendment enabled on a test network, then a live bridge creation and transfer observed read-only |
| G-04 | Witness set and SignerList of any future door account | No bridge exists, so there is no door account to inspect | A created bridge, then account_objects / signer_list on its door accounts |
| G-05 | Vote counts and activation ETA for XChainBridge | The public feature RPC exposes no vote counts; the VHS vote endpoint was not queried in this pack | A VHS vote-endpoint read, or operator disclosure of validator voting intent |
| G-06 | Audit status of the pfUSDC contracts and zkVM programs | Different repository (postfiatl1v2); the pfUSDC page itself lists third-party audits as remaining work | Published audit reports for the pfUSDC vault, verifier, and guest programs |
| G-07 | Exact rounding behaviour of the reward split without the fix | The ambient Number::getround() mode on the live node is not observable from outside | A run of the pinned code with fixXChainRewardRounding disabled, or operator disclosure of the rounding mode |
