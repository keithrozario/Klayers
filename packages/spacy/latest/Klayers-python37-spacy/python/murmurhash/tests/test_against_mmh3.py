import mmh3
import murmurhash.mrmr


def test_hash32_matches_mmh3():
    string = "hello world"
    assert mmh3.hash(string) == murmurhash.mrmr.hash(string)
    string = "anxiety"
    assert mmh3.hash(string) == murmurhash.mrmr.hash(string)
