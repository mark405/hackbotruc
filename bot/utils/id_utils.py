def load_ids(filepath='data/valid_ids.txt'):
    try:
        with open(filepath, 'r') as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_ids(ids, filepath='data/valid_ids.txt'):
    with open(filepath, 'w') as f:
        f.write('\n'.join(sorted(ids)))

def add_id(new_id, filepath='data/valid_ids.txt'):
    ids = load_ids(filepath)
    ids.add(str(new_id))
    save_ids(ids)

def remove_id(id_to_remove, filepath='data/valid_ids.txt'):
    ids = load_ids(filepath)
    ids.discard(str(id_to_remove))
    save_ids(ids)
