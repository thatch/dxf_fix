from setuptools import setup

with open("README.md") as f:
    readme = f.read()

with open("dxf_fix/__init__.py") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split('"')[1]

with open("requirements.txt") as f:
    requires = f.read().strip().splitlines()

setup(
    name="dxf_fix",
    description="Fixer for dxf files like those output by openscad",
    long_description=readme,
    long_description_content_type="text/markdown",
    version=version,
    author="Tim Hatch",
    author_email="tim@timhatch.com",
    url="https://github.com/thatch/dxf_fix",
    license="BSD",
    packages=("dxf_fix",),
    setup_requires=["setuptools"],
    install_requires=requires,
    entry_points={"console_scripts": ["dxf_fix = dxf_fix:main"]},
)
