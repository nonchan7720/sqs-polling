from setuptools import find_packages, setup


def read_file(filename: str) -> str:
    with open(filename, "r") as f:
        return f.read()


setup(
    name="sqs-apolling",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    author="Nozomi nishinohara",
    author_email="nozomi_nishinohara@n-creativesystem.com",
    description="Poll AWS SQS using asyncio and execute callback.",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    project_urls={
        "Code": "https://github.com/nonchan7720/sqs-polling",
        "Tracker": "https://github.com/nonchan7720/sqs-polling/issues",
    },
    url="https://github.com/nonchan7720/sqs-polling",
    packages=find_packages(exclude=["tests*"]),
    install_requires=["boto3", "asyncio"],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Topic :: System :: Distributed Computing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
    entry_points={"console_scripts": ["sqs_apolling = sqs_polling.__main__:main"]},
    license=read_file("LICENSE"),
)
