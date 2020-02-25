from setuptools import setup
import glob


setup(
    name="ssdppot",
    author="Teemu Rytilahti",
    version="0.1",
    py_modules=["ssdppot"],
    install_requires=["click", "motor", "cachetools", "tqdm", "aiohttp==3.4.4"],
    package_data={"ssdppot": [glob.glob("ssdppot/data/*")]},
    entry_points="""
        [console_scripts]
        ssdppot=ssdppot.httpserver:cli
        udpresponder=ssdppot.udpserver:cli
    """,
)
