from setuptools import setup, find_packages

setup(
    name="energyos",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        'numpy>=1.21.0',
        'pandas>=1.3.0',
        'matplotlib>=3.4.0',
        'pvlib>=0.9.0',
        'requests>=2.26.0',
        'python-dateutil>=2.8.2'
    ],
    python_requires='>=3.9',
)
