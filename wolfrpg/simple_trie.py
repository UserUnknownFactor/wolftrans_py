from .service_fn import normalize_n

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.command_type = None
        self.coordinates = []
        self.line_indexes = []

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, string: str, command_type: str, coordinate: tuple, line_index: int):
        node = self.root
        for char in normalize_n(string, True):
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True
        node.command_type = command_type
        node.line_indexes.append(line_index)
        node.coordinates.append(coordinate)  # store all occurrences of this string

    def search(self, string: str) -> TrieNode | None:
        node = self.root
        for char in normalize_n(string, True):
            if char not in node.children:
                return None
            node = node.children[char]
        return node if node.is_end else None
