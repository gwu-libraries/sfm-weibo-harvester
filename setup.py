from setuptools import setup

setup(
    name='sfmweiboharvester',
    version='0.1.0',
    url='https://github.com/gwu-libraries/sfm-weibo-harvester',
    author='Vict Tan',
    author_email='tanych5233@gmail.com',
    description="Social Feed Manager Weibo Harvester",
    platforms=['POSIX'],
    py_modules=['weibo_harvester',],
    install_requires=['sfmutils', 'weibowarc'],
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2.7',
        'Development Status :: 4 - Beta',
    ],
)