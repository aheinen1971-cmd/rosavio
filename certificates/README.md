# Rose update verification certificate

rose-update.der is the public RSA-4096 certificate embedded into Rose's native
updater. It verifies Rose MAR packages signed with SHA-384. The corresponding
encrypted private key is stored separately and must never be committed or
included in a browser download.

SHA-256 certificate fingerprint:
FD9C5E464C616224129E9E2A30405FD73CCAB568577A7FF05B9ECE6D135DC6BE
