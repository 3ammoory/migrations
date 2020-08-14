import setuptools

setuptools.setup(
    name="smg-3ammoory",  # Replace with your own username
    version="0.0.1",
    author="3ammoory",
    author_email="omarabobakr2973@gmail.com",
    description="A migrations tool for postgresql databases with multiple schemas",
    url="https://github.com/3ammoory/migrations",
    install_requires=[
        'typer',
        'asyncpg',
        'python-dotenv',
        'sqlparse'
    ],
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": ["smg = smg.smg:app"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
