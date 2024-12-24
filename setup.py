from setuptools import setup, find_packages

setup(
    name="llmfs",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fusepy",
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=0.19.0",
        "python-daemon>=3.0.0",
    ],
    entry_points={
        'console_scripts': [
            'llmfs=llmfs.__main__:main',
        ],
    },
    python_requires='>=3.6',
    description="A memory filesystem backed by JSON",
    author="Cline",
)
