import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
  name="cyberlink",
  version="0.1.0.dev2",
  author="Diving Fish",
  author_email="dfyshisb@163.com",
  description="A light, asynchronous websocket server written by Python",
  long_description=long_description,
  long_description_content_type="text/markdown",
  url="https://github.com/Diving-Fish/cyberlink",
  packages=setuptools.find_packages(),
  classifiers=[
  "Programming Language :: Python :: 3",
  "License :: OSI Approved :: MIT License",
  "Operating System :: OS Independent",
  ],
  python_requires='>=3.7'
)