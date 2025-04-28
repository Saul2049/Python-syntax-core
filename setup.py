from setuptools import setup, find_packages

setup(
    name="trading_framework",
    version="0.1.0",
    description="A modular Python framework for backtesting algorithmic trading strategies",
    author="Saul2049",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pandas>=2.1.4",
        "numpy>=1.26.3",
        "matplotlib>=3.8.2",
        "tqdm>=4.66.1",
        "requests>=2.32.0",
        "python-dateutil>=2.9.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
) 