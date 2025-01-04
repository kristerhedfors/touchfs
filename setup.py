from setuptools import setup, find_packages

setup(
    name="touchfs",
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
            'touchfs_mount=touchfs.__main__:run',
            'touchfs_context=touchfs.cli.context_command:run',
            'touchfs_generate=touchfs.cli.generate_command:run',
        ],
    },
    python_requires='>=3.6',
    description="A memory filesystem backed by JSON",
    author="Cline",
)
