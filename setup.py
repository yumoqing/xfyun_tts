try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

with open('xfyun_tts/version.py', 'r') as f:
	x = f.read()
	y = x[x.index("'")+1:]
	z = y[:y.index("'")]
	version = z
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
	name='xfyun_tts',
	packages=['xfyun_tts'],
	version=version,
	description='a pyttsx3 driver for baidu device, it use baidu.speech.tts.',
	long_description=long_description,
	long_description_content_type="text/markdown",
	author='Yu Moqing',
	url='https://github.com/yumoqing/xfyun_tts',
	author_email='yumoqing@gmail.com',
	# install_requires=install_requires ,
	keywords=['pyttsx' , 'baidu', 'offline tts engine'],
	classifiers = [
		  'Intended Audience :: End Users/Desktop',
		  'Intended Audience :: Developers',
		  'Intended Audience :: Information Technology',
		  'Intended Audience :: System Administrators',
		  'Operating System :: OS Independent',
		  'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
		  'Programming Language :: Python :: 3'
	],
)
