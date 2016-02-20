from nose.tools import *
#import NAME
#  all function with test will be tested
# running: cd this dir and then nosetests 
# or 
# nosetests -w workdir
# nosetests -s，不捕获输出，会让你的程序里面的一些命令行上的输出显示出来。例如print所输出的内容。
# 
# if __name__ =='__main__': 
#      nose.main()

class TestClass():
	def setUp(self):
		print "SETUP!"

	def tearDown(self):
		print "TEAR DOWN!"

	def test_basic(self):
		print "I RAN in TestClass!"

class TestClass2():
	def setUp(self):
		print "SETUP!"

	def tearDown(self):
		print "TEAR DOWN!"

	def test_basic(self):
		print "I RAN in TestClass2!"