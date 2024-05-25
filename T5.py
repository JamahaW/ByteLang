def D(n, m):
    return n % m == 0

def main():

    N = range(1, int(1e5))

    for A in N:
        if all((D(72, x) <= (not D(120, x))) or ((A - x) > 100)  for x in N):
            print(A)
            break

    return

main()