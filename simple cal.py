a=float(input('Enter first value='))
sign=input('Enter sign value=')
b=float(input('Enter second value='))
if sign == '+':
    print('Result=',a+b)
elif sign == '-':
    print('Result=',a-b)
elif sign == '*':
    print('Result=',a*b)
elif sign == '%':
    print('Result=',a%b)
elif sign == '/':
    print('Result=',a/b)
else:
    print('enter valid sign value')