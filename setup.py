from setuptools import setup, find_packages

setup(
    name="llmfs",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fusepy",
    ],
    entry_points={
        'console_scripts': [
            'llmfs=llmfs.llmfs:main',
        ],
    },
    python_requires='>=3.6',
    description="A memory filesystem backed by JSON",
    author="Cline",
)
