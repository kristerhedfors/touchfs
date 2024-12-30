fve rom setuptools import setup, find_packages

setup(
    name="llmfs",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "fusepy",
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=0.19.0",
        "python-daemon>=3.0.0",
        "tiktoken>=0.5.0",
    ],
    entry_points={
        'console_scripts': [
            'llmfs_mount=llmfs.__main__:run',
            'llmfs_context=llmfs.cli.context_command:run',
        ],
    },
    python_requires='>=3.6',
    description="A memory filesystem backed by JSON",
    author="Cline",
)
