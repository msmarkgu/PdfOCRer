from setuptools import setup, find_packages

setup(
    name='PdfOCRer',             # Replace with your package name
    version='1.2',               # Version of your package
    author='Mark Gu',            # Your name
    author_email='mark.reachee@gmail.com', # Your email
    description='A Python script that runs Paddle OCR on a possibly unsearchable PDF to make it searchable. ',
    long_description=open('README.md').read(), # Read long description from README
    long_description_content_type='text/markdown',
    url='https://github.com/msmarkgu/PdfOCRer', # Your package URL
    packages=find_packages(),             # Automatically find packages
    install_requires=[                    # List of dependencies
        'pypdf2',
        'pillow',
        'reportlab',
        'paddleocr',
        'paddlepaddle',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License', # Adjust as necessary
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',              # Minimum Python version
)
