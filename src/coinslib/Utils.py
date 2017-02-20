from Crypto.Hash import SHA256


def wallet_id_from_public_key(public_key):
    hasher = SHA256.new()
    hasher.update(public_key.exportKey(format='DER'))
    return hasher.hexdigest()


def seed_from_hash(hash_string):
    hash_prefix = hash_string[0:16]
    int_hex = ""
    for i in range(int(len(hash_prefix)/2)):
        byte_hex = hash_prefix[i*2:(i*2)+2]
        int_hex = "{0}{1}".format(byte_hex, int_hex)
    return int(int_hex, 16)
