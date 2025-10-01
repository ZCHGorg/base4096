from setuptools import setup

setup(
    name='base4096',
    version='2.1.1',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['*.py'],
    },
    description='Base4096 encoding and decoding functions',
    author='Josef Kulovany',
    author_email='charg.chg.wecharg@gmail.com',
    url='https://github.com/ZCHGorg/base4096',
    license='https://zchg.org/t/legal-notice-copyright-applicable-ip-and-licensing-read-me/440',
    keywords='base4096 encoder decoder',
    install_requires=[],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: ZCHG.ORG LICENSE - https://zchg.org/t/legal-notice-copyright-applicable-ip-and-licensing-read-me/440',
        'Operating System :: OS Independent',
    ],
)
