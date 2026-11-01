"""Download the two verified datasets only; never retrieve model code."""
import hashlib
from io import BytesIO
from pathlib import Path
import sys
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SOURCES={
 'filmtrust': (
  'https://guoguibing.github.io/librec/datasets/filmtrust.zip',
  'filmtrust',
  {'ratings.txt':'241167424e24d588e8871d68641e94ead98d5b3a4f0db01ef3181a74ad35e7a1',
   'trust.txt':'64573a033add72b988a0fb140fdbc0ad3464cb9821f940007aff6fda44b09603'}),
 'epinions': (
  'https://static.preferred.ai/cornac/datasets/epinions/ratings_data.zip',
  'epinions_665k',
  {'ratings_data.txt':'6da14f79369cf882911a271efd5f4575bc4292d0497ccf3190b6421a6d198e42',
   'trust_data.txt':'7562075fdcc27d04cd1d88d592e04f4fa57e5d7043246187789d0ccc3e1985f0'})
}


def obtain(name):
    url, folder, hashes=SOURCES[name]
    destination=ROOT/'datasets'/folder
    if all((destination/n).exists() and hashlib.sha256((destination/n).read_bytes()).hexdigest()==h
           for n,h in hashes.items()):
        print(name,'already verified')
        return
    with urllib.request.urlopen(url,timeout=60) as response:
        payload=response.read()
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        mapping={Path(n).name:n for n in archive.namelist() if not n.endswith('/')}
        contents={name:archive.read(mapping[name]) for name in hashes}
        for name,expected in hashes.items():
            actual=hashlib.sha256(contents[name]).hexdigest()
            if actual!=expected:
                raise ValueError(f'{url}: hash mismatch for {name}, downloaded content was NOT installed')
        destination.mkdir(parents=True,exist_ok=True)
        for name,content in contents.items():
            p=destination/name
            if p.exists() and p.read_bytes()!=content:
                raise FileExistsError(f'Refusing to overwrite different existing data: {p}')
            p.write_bytes(content)
    print(folder,'downloaded and verified')


if __name__=='__main__':
    for name in sys.argv[1:] or SOURCES:
        obtain(name)
