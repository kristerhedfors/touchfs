from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="touchfs",
    version="0.2.0",
    author="Krister Hedfors",
    author_email="krister.hedfors@gmail.com",
    description="A context-aware filesystem that generates content on demand using LLMs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kristerhedfors/touchfs",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: System :: Filesystems",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fusepy",
        "pytest>=7.0.0",
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=0.19.0",
        "PyYAML>=6.0.0",
        "tiktoken>=0.5.0",
        "psutil>=5.9.0",
    ],
    entry_points={
        "console_scripts": [
            "touchfs=touchfs.cli.touchfs_cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "touchfs": [
            "templates/prompts/*.system_prompt",
        ],
    },
)
