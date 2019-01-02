from setuptools import setup

setup(
    name='sfmweiboharvester',
    version='2.0.2',
    url='https://github.com/gwu-libraries/sfm-weibo-harvester',
    author='Social Feed Manager',
    author_email='sfm@gwu.edu',
    description="Social Feed Manager Weibo Harvester",
    platforms=['POSIX'],
    test_suite='tests',
    scripts=['weibo_harvester.py',
             'weiboarc.py',
             'weibo_warc_iter.py'],
    py_modules=['weibo_harvester','weiboarc','weibo_warc_iter'],
    install_requires=['sfmutils'],
    tests_require=['mock==2.0.0'],
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
    ],
)
