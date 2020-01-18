import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="visidata_plugins_ajkerrigan",
    version="0.0.1",
    author="AJ Kerrigan",
    author_email="kerrigan.aj@gmail.com",
    description="VisiData plugins",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ajkerrigan/visidata-plugins",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
