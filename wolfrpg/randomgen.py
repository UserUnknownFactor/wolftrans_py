def bytes_to_u2_array(data: bytes, length: int) -> list[int]:
    return [int.from_bytes(data[i:i+2], 'little') for i in range(0, length * 2, 2)]

def u2_array_to_bytes(words: list[int]) -> bytes:
    return b''.join((words[i] & 0xFFFF).to_bytes(2, 'little') for i in range(len(words)))

def simulate_seed_0():
  import time, calendar
  timestamp = calendar.timegm(time.gmtime())
  timestamp = timestamp & 0xFFFFFFFF
  return timestamp

def print_source_time(unix_timestamp):
  import time
  source_time = time.gmtime(unix_timestamp)
  formatted_time = time.strftime("%Y-%m-%d %H:%M:%S UTC", source_time)
  print(f"Source Time: {formatted_time}")

def generate_randoms(old_offset: int, old_u4_1: int, old_u4_2: int, new_offset: int, randoms_len: int, old_randoms: bytes, hid_pos_len:int) -> tuple[int, int, bytes]:
    pos2 = old_offset + 4 + 4 # pos after old_u4_1, old_u4_2

    # On second thought, we just need to mod old_u4's and the obfuscated offsets, lol
    offset_diff = new_offset - old_offset
    _pos_obfs_positions = old_randoms[old_u4_2 - pos2 : old_u4_2 - pos2 + hid_pos_len * 2]
    _pos_obfs_pos_array = bytes_to_u2_array(_pos_obfs_positions, hid_pos_len)
    _pos_obfs_pos_array = [i + offset_diff for i in _pos_obfs_pos_array]

    new_randoms = bytearray(old_randoms[:])
    new_randoms[old_u4_2 - pos2 : old_u4_2 - pos2 + hid_pos_len * 2] = u2_array_to_bytes(_pos_obfs_pos_array)

    old_u4_1 += offset_diff
    old_u4_2 += offset_diff
    return old_u4_1, old_u4_2, bytes(new_randoms)


    # NOTE: I will keep this as research for finding seeds from LCG pseudo-randoms
    from .wcrypto import srand, rand, KC0, KC1, KC2, RAND_MULTIPLIER, RAND_INCREMENT, RAND_MAX, MAX_INT32
    import pickle, os

    PICKLE_CACHE = "seed_found.dat"

    _pos_rands_bytes = old_randoms[old_u4_1 - pos2 : old_u4_1 - pos2 + hid_pos_len * 2]
    _pos_rands_array = bytes_to_u2_array(_pos_rands_bytes, hid_pos_len)
    _pos_obfs_positions = old_randoms[old_u4_2 - pos2 : old_u4_2 - pos2 + hid_pos_len * 2]
    _pos_obfs_pos_array = bytes_to_u2_array(_pos_obfs_positions, hid_pos_len)
    _positions = [(a + b - pos2) & 0xFFFF for a, b in zip(_pos_obfs_pos_array, _pos_rands_array)]

    min_bytes = min(min(_positions), 128)
    seed_0_val = None
    if os.path.exists(PICKLE_CACHE):
        try:
            with open(PICKLE_CACHE, "rb") as f:
                seed_0_val = pickle.load(f)
                if not isinstance(seed_0_val, int):
                    raise TypeError("Seed must be an integer.")
        except (pickle.UnpicklingError, TypeError):
            pass

    if seed_0_val is None:
        from z3 import z3, Solver, BitVecs # requires: pip install z3-solver

        def get_solutions(s: z3.Solver):
            result = s.check()
            while (result == z3.sat):
                m = s.model()
                yield m
                block = []
                for var in m:
                    block.append(var() != m[var])
                s.add(z3.Or(block))
                result = s.check()

        # Z3 maths part
        seed_0, r1, r2, K1, K2 = BitVecs('seed_0 r1 r2 K1 K2', 32)

        # Define seed_1 and seed_2 in terms of seed_0
        seed_1 = (RAND_MULTIPLIER * seed_0 + RAND_INCREMENT) & MAX_INT32
        seed_2 = (RAND_MULTIPLIER * seed_1 + RAND_INCREMENT) & MAX_INT32

        # Create constraints based on the known values and rand() formula
        s = Solver()
        s.add(r1 == (seed_1 >> 16) & RAND_MAX)
        s.add(r2 == (seed_2 >> 16) & RAND_MAX)
        s.add(K1 == r1 % KC0)
        s.add(K2 == r2 % KC0)
        s.add(old_u4_1 == K1 + old_offset + KC1)
        s.add(old_u4_2 == old_u4_1 + K2 + old_offset + 4 + KC2)

        upper_bound = MAX_INT32
        for solution, _ in zip(get_solutions(s), range(upper_bound)):
            seed_0_val = solution[seed_0].as_long()
            # Validate the result
            srand(seed_0_val)
            r1 = rand() % KC0 + old_offset + KC1
            r2 = r1 + rand() % KC0 + old_offset + 4 + KC2
            assert old_u4_1 == r1 and old_u4_2 == r2, (
                f"Incorrect result: R1: {r1} ({old_u4_1}) R2: {r2} ({old_u4_2})")
            if any( (rand() >> 8) & 0xFF != old_randoms[i] for i in range(min_bytes)):
                continue
            print("Found Game.dat seed:", seed_0_val)
            with open(PICKLE_CACHE, 'wb') as f:
                pickle.dump(seed_0_val, f)
            break
        else:
            print("No seed solution found")
            return None, None, None
    else:
        print("Using Game.dat seed:", seed_0_val)

    srand(seed_0_val)
    _old_positions = _positions[:]
    # NOTE: The commented code is for info only, as we are solving for a later seed
    #_positions = []
    #_pos_obfs_pos_array = []
    #_pos_rands_array = []

    #for _ in range(hid_pos_len):
        #_positions.add((rand() & 0xFF00 + rand() >> 8 & 0xFF) % 18000 + new_offset + 100)
    #for i in range(hid_pos_len):
        #pos_rand =  rand() >> 8 & 0xFF + rand() & 0xFF00
        #_pos_rands_array.append(pos_rand)
        #obf_pos = _positions[i] - pos_rand
        #_pos_obfs_pos_array.append(obf_pos)

    r1 = rand() % KC0 + new_offset + KC1
    r2 = r1 + rand() % KC0 + new_offset + 4 + KC2
    new_randoms = bytearray((rand() >> 8 & 0xFF) for _ in range(randoms_len))

    pos2 = new_offset + 4 + 4
    insert_pos = r1 - pos2
    new_randoms[insert_pos:insert_pos] = _pos_rands_bytes
    insert_pos = r2 - pos2
    offset_diff = new_offset - old_offset

    _pos_obfs_pos_array = [i + offset_diff for i in _pos_obfs_pos_array]
    new_randoms[insert_pos:insert_pos] = u2_array_to_bytes(_pos_obfs_pos_array)

    _positions = [(a + b - pos2) & 0xFFFF for a, b in zip(_pos_obfs_pos_array, _pos_rands_array)]
    for i, pos in enumerate(_old_positions):
        new_randoms[_positions[i]] = old_randoms[pos]

    new_randoms = new_randoms[:len(old_randoms)]
    return r1, r2, new_randoms
