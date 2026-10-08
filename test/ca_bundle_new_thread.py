import threading

import certifi

import pyproj

pyproj.network.set_ca_bundle_path(certifi.where())
size = len(certifi.where().encode())
junk = [b"x" * size + bytes([n % 256]) for n in range(100_000)]


def convert(results):
    transformer = pyproj.Transformer.from_crs("EPSG:4267", "EPSG:4269", always_xy=True)
    results.append(transformer.transform(-79.4, 43.65))


results = []
thread = threading.Thread(target=convert, args=(results,))
thread.start()
thread.join()
assert all(abs(value) < 180 for value in results[0]), results[0]
