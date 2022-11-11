class A:
  one = 1
  @classmethod
  def funcOne(cls, inval: float = None):
    print("funcOne", inval, cls.one)
  @classmethod
  def funcTwo(cls, inval: float = None):
    print("funcTwo", inval, cls.one, cls.funcOne(inval))

class B(A):
  one = 2

first = A()
second = B()
# first.funcOne()
# second.funcOne()
# A.funcOne()
# B.funcOne()

# N = 4
# for i in range(N):
#   for j in range(i+1, N):
#     print(i, j)

print(first == A)
print(first is A)
print(first.__class__ == A)
print(first.__class__ is A)
print(isinstance(first, A))
print(isinstance(second, A))
print(isinstance(first, B))
print(isinstance(second, B))