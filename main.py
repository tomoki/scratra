#!/usr/bin/env python
#coding:utf-8

# Before running program,run Scratch and enable external sensor.
#  See http://tkamada.blogspot.jp/2011/06/scratch.html
from scratra import *

@start
def whenstart(scratch):
    print("Hello World")

@broadcast(r"Hi.*")
def hi(scratch,msg):
    print(msg)
    scratch.broadcast("hoge")

@update(r"poyo")
def poyo(scratch,var,val):
    print("hoge",scratch.var("hoge"))
    print(var,val)

# @update(r".*")
# def all_var(scratch,var,val):
#     print(var,val)

@end
def whenend(scratch):
    print("Goodbye World")


run()
