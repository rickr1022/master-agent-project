from setuptools import setup, find_packages

setup(
    name="master_agent",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'python-dotenv',
        'pandas',
        'numpy',
        'requests',
        'google-cloud-storage',
        'flask'
    ],
)