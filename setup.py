from setuptools import setup, find_packages

setup(
    name="crypto_trading_bot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "ta",
        "python-dotenv",
        "requests",
        "matplotlib",
        "seaborn",
    ],
) 