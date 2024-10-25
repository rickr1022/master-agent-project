from setuptools import find_packages, setup

setup(
    name="master_agent",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "pandas",
        "numpy",
        "requests",
        "google-cloud-storage",
        "flask",
    ],
)
