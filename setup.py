from setuptools import setup

setup(
    name='base4096',
    version='2.0',
    py_modules=[
        'base4096',
        'base4096_shim',
        'frozen_base4096_alphabet',
        'freeze_base4096_alphabet',
        'sign_base4096',
        'base4096_hkdf_seal',
    ],
    packages=['base4096'],  # Only if you include base4096/__init__.py
    include_package_data=True,
    package_data={'': ['*.txt']},
    description='Base4096 encoding and decoding functions',
    author='Josef Kulovany',
    author_email='charg.chg.wecharg@gmail.com',
    url='https://github.com/ZCHGorg/base4096',
    license='https://zchg.org/t/legal-notice-copyright-applicable-ip-and-licensing-read-me/440',
    keywords='base4096 encoder decoder',
    install_requires=[],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: Other/Proprietary License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
