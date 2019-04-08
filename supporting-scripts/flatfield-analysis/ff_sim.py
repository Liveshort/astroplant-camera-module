import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # sim resolution
    n = 100

    # kit parameters
    h = 0.31#0.63
    w = 0.41
    r = w/2
    R = 0.65

    # initial brightness of perfect diffuse light source in the middle of the top plate
    I0 = 1.0

    # set up grid arrays
    x = np.linspace(-15*r, 15*r, 15*n)
    y = np.linspace(-15*r, 15*r, 15*n)
    xv, yv = np.meshgrid(x, y, sparse=False, indexing='xy')

    # calculate distance in the ground plane
    dist_gp = np.square(xv) + np.square(yv)
    # calculate distance to light source
    dist = dist_gp + h*h
    # calculate light multiplication factor due to angle (Lambertian diffuse reflection)
    lamb = np.cos(np.arctan(dist_gp/(h*h)))

    # invert to obtain intensities, multiply with lambertian factor twice, once for the emission (which is already a diffuse reflection off a surface, and once more to correct for the second diffuse reflection on the white bottom plane)
    first_order = np.multiply(np.divide(I0*np.ones_like(dist), dist), np.square(lamb))
    # calculate second order
    second_order = np.zeros([n,n])
    second_order += R*np.flip(first_order[6*n:7*n, 7*n:8*n], 0)
    second_order += R*np.flip(first_order[8*n:9*n, 7*n:8*n], 0)
    second_order += R*np.flip(first_order[7*n:8*n, 6*n:7*n], 1)
    second_order += R*np.flip(first_order[7*n:8*n, 8*n:9*n], 1)
    # calculate third order
    third_order = np.zeros([n,n])
    third_order += R*R*first_order[5*n:6*n, 7*n:8*n]
    third_order += R*R*first_order[9*n:10*n, 7*n:8*n]
    third_order += R*R*first_order[7*n:8*n, 5*n:6*n]
    third_order += R*R*first_order[7*n:8*n, 9*n:10*n]
    third_order += R*R*np.flip(np.flip(first_order[6*n:7*n, 6*n:7*n], 0), 1)
    third_order += R*R*np.flip(np.flip(first_order[8*n:9*n, 6*n:7*n], 0), 1)
    third_order += R*R*np.flip(np.flip(first_order[6*n:7*n, 8*n:9*n], 0), 1)
    third_order += R*R*np.flip(np.flip(first_order[8*n:9*n, 8*n:9*n], 0), 1)
    # calculate fourth order
    fourth_order = np.zeros([n,n])
    fourth_order += R*R*R*np.flip(first_order[4*n:5*n, 7*n:8*n], 0)
    fourth_order += R*R*R*np.flip(first_order[10*n:11*n, 7*n:8*n], 0)
    fourth_order += R*R*R*np.flip(first_order[7*n:8*n, 4*n:5*n], 1)
    fourth_order += R*R*R*np.flip(first_order[7*n:8*n, 10*n:11*n], 1)
    fourth_order += R*R*R*np.flip(first_order[6*n:7*n, 5*n:6*n], 0)
    fourth_order += R*R*R*np.flip(first_order[6*n:7*n, 9*n:10*n], 0)
    fourth_order += R*R*R*np.flip(first_order[8*n:9*n, 5*n:6*n], 0)
    fourth_order += R*R*R*np.flip(first_order[8*n:9*n, 9*n:10*n], 0)
    fourth_order += R*R*R*np.flip(first_order[5*n:6*n, 6*n:7*n], 1)
    fourth_order += R*R*R*np.flip(first_order[9*n:10*n, 6*n:7*n], 1)
    fourth_order += R*R*R*np.flip(first_order[5*n:6*n, 8*n:9*n], 1)
    fourth_order += R*R*R*np.flip(first_order[9*n:10*n, 8*n:9*n], 1)
    # calculate fifth order
    fifth_order = np.zeros([n,n])
    fifth_order += R*R*R*R*first_order[3*n:4*n, 7*n:8*n]
    fifth_order += R*R*R*R*first_order[11*n:12*n, 7*n:8*n]
    fifth_order += R*R*R*R*first_order[7*n:8*n, 3*n:4*n]
    fifth_order += R*R*R*R*first_order[7*n:8*n, 11*n:12*n]
    fifth_order += R*R*R*R*first_order[5*n:6*n, 5*n:6*n]
    fifth_order += R*R*R*R*first_order[5*n:6*n, 9*n:10*n]
    fifth_order += R*R*R*R*first_order[9*n:10*n, 5*n:6*n]
    fifth_order += R*R*R*R*first_order[9*n:10*n, 9*n:10*n]
    fifth_order += R*R*R*R*np.flip(np.flip(first_order[6*n:7*n, 4*n:5*n], 0), 1)
    fifth_order += R*R*R*R*np.flip(np.flip(first_order[6*n:7*n, 10*n:11*n], 0), 1)
    fifth_order += R*R*R*R*np.flip(np.flip(first_order[8*n:9*n, 4*n:5*n], 0), 1)
    fifth_order += R*R*R*R*np.flip(np.flip(first_order[8*n:9*n, 10*n:11*n], 0), 1)
    fifth_order += R*R*R*R*np.flip(np.flip(first_order[4*n:5*n, 6*n:7*n], 1), 0)
    fifth_order += R*R*R*R*np.flip(np.flip(first_order[10*n:11*n, 6*n:7*n], 1), 0)
    fifth_order += R*R*R*R*np.flip(np.flip(first_order[4*n:5*n, 8*n:9*n], 1), 0)
    fifth_order += R*R*R*R*np.flip(np.flip(first_order[10*n:11*n, 8*n:9*n], 1), 0)
    # calculate sixth order
    sixth_order = np.zeros([n,n])
    sixth_order += R*R*R*R*R*np.flip(first_order[2*n:3*n, 7*n:8*n], 0)
    sixth_order += R*R*R*R*R*np.flip(first_order[12*n:13*n, 7*n:8*n], 0)
    sixth_order += R*R*R*R*R*np.flip(first_order[7*n:8*n, 2*n:3*n], 1)
    sixth_order += R*R*R*R*R*np.flip(first_order[7*n:8*n, 12*n:13*n], 1)
    sixth_order += R*R*R*R*R*np.flip(first_order[4*n:5*n, 5*n:6*n], 0)
    sixth_order += R*R*R*R*R*np.flip(first_order[4*n:5*n, 9*n:10*n], 0)
    sixth_order += R*R*R*R*R*np.flip(first_order[10*n:11*n, 5*n:6*n], 0)
    sixth_order += R*R*R*R*R*np.flip(first_order[10*n:11*n, 9*n:10*n], 0)
    sixth_order += R*R*R*R*R*np.flip(first_order[5*n:6*n, 4*n:5*n], 1)
    sixth_order += R*R*R*R*R*np.flip(first_order[5*n:6*n, 10*n:11*n], 1)
    sixth_order += R*R*R*R*R*np.flip(first_order[9*n:10*n, 4*n:5*n], 1)
    sixth_order += R*R*R*R*R*np.flip(first_order[9*n:10*n, 10*n:11*n], 1)
    sixth_order += R*R*R*R*R*np.flip(first_order[6*n:7*n, 3*n:4*n], 0)
    sixth_order += R*R*R*R*R*np.flip(first_order[6*n:7*n, 11*n:12*n], 0)
    sixth_order += R*R*R*R*R*np.flip(first_order[8*n:9*n, 3*n:4*n], 0)
    sixth_order += R*R*R*R*R*np.flip(first_order[8*n:9*n, 11*n:12*n], 0)
    sixth_order += R*R*R*R*R*np.flip(first_order[3*n:4*n, 6*n:7*n], 1)
    sixth_order += R*R*R*R*R*np.flip(first_order[11*n:12*n, 6*n:7*n], 1)
    sixth_order += R*R*R*R*R*np.flip(first_order[3*n:4*n, 8*n:9*n], 1)
    sixth_order += R*R*R*R*R*np.flip(first_order[11*n:12*n, 8*n:9*n], 1)
    # calculate seventh order
    seventh_order = np.zeros([n,n])
    seventh_order += R*R*R*R*R*R*first_order[n:2*n, 7*n:8*n]
    seventh_order += R*R*R*R*R*R*first_order[13*n:14*n, 7*n:8*n]
    seventh_order += R*R*R*R*R*R*first_order[7*n:8*n, n:2*n]
    seventh_order += R*R*R*R*R*R*first_order[7*n:8*n, 13*n:14*n]
    seventh_order += R*R*R*R*R*R*np.flip(np.flip(first_order[4*n:5*n, 4*n:5*n], 0), 1)
    seventh_order += R*R*R*R*R*R*np.flip(np.flip(first_order[4*n:5*n, 10*n:11*n], 0), 1)
    seventh_order += R*R*R*R*R*R*np.flip(np.flip(first_order[10*n:11*n, 4*n:5*n], 0), 1)
    seventh_order += R*R*R*R*R*R*np.flip(np.flip(first_order[10*n:11*n, 10*n:11*n], 0), 1)
    seventh_order += R*R*R*R*R*R*first_order[5*n:6*n, 3*n:4*n]
    seventh_order += R*R*R*R*R*R*first_order[5*n:6*n, 11*n:12*n]
    seventh_order += R*R*R*R*R*R*first_order[9*n:10*n, 3*n:4*n]
    seventh_order += R*R*R*R*R*R*first_order[9*n:10*n, 11*n:12*n]
    seventh_order += R*R*R*R*R*R*first_order[3*n:4*n, 5*n:6*n]
    seventh_order += R*R*R*R*R*R*first_order[11*n:12*n, 5*n:6*n]
    seventh_order += R*R*R*R*R*R*first_order[3*n:4*n, 9*n:10*n]
    seventh_order += R*R*R*R*R*R*first_order[11*n:12*n, 9*n:10*n]
    seventh_order += R*R*R*R*R*R*np.flip(first_order[2*n:3*n, 6*n:7*n], 1)
    seventh_order += R*R*R*R*R*R*np.flip(first_order[12*n:13*n, 6*n:7*n], 1)
    seventh_order += R*R*R*R*R*R*np.flip(first_order[6*n:7*n, 2*n:3*n], 0)
    seventh_order += R*R*R*R*R*R*np.flip(first_order[6*n:7*n, 12*n:13*n], 0)
    seventh_order += R*R*R*R*R*R*np.flip(first_order[2*n:3*n, 8*n:9*n], 1)
    seventh_order += R*R*R*R*R*R*np.flip(first_order[12*n:13*n, 8*n:9*n], 1)
    seventh_order += R*R*R*R*R*R*np.flip(first_order[8*n:9*n, 2*n:3*n], 0)
    seventh_order += R*R*R*R*R*R*np.flip(first_order[8*n:9*n, 12*n:13*n], 0)

    print(xv)
    print(yv)

    # calculate view on center field
    field = np.zeros([2*n, 2*n])
    field[n//2:3*n//2, n//2:3*n//2] += first_order[7*n:8*n, 7*n:8*n]
    field[n//2:3*n//2, n//2:3*n//2] += second_order
    field[n//2:3*n//2, n//2:3*n//2] += third_order
    field[n//2:3*n//2, n//2:3*n//2] += fourth_order
    field[n//2:3*n//2, n//2:3*n//2] += fifth_order
    field[n//2:3*n//2, n//2:3*n//2] += sixth_order
    field[n//2:3*n//2, n//2:3*n//2] += seventh_order
    # calculate view on reflective surfaces
    field[0:n//2, n//2:3*n//2] = R*np.flip(field[n//2:n, n//2:3*n//2], 0)
    field[3*n//2:2*n, n//2:3*n//2] = R*np.flip(field[2*n//2:3*n//2, n//2:3*n//2], 0)
    field[n//2:3*n//2, 0:n//2] = R*np.flip(field[n//2:3*n//2, n//2:n], 1)
    field[n//2:3*n//2, 3*n//2:2*n] = R*np.flip(field[n//2:3*n//2, 2*n//2:3*n//2], 1)
    # calculate view on second order reflective surfaces
    field[0:n//2, 0:n//2] = R*R*np.flip(np.flip(field[n//2:n, n//2:n], 0), 1)
    field[3*n//2:2*n, 0:n//2] = R*R*np.flip(np.flip(field[n:3*n//2, n//2:n], 0), 1)
    field[0:n//2, 3*n//2:2*n] = R*R*np.flip(np.flip(field[n//2:n, n:3*n//2], 0), 1)
    field[3*n//2:2*n, 3*n//2:2*n] = R*R*np.flip(np.flip(field[n:3*n//2, n:3*n//2], 0), 1)

    plt.figure()
    plt.subplot(2,4,1)
    plt.imshow(first_order)
    plt.colorbar()
    plt.subplot(2,4,2)
    plt.imshow(second_order)
    plt.colorbar()
    plt.subplot(2,4,3)
    plt.imshow(third_order)
    plt.colorbar()
    plt.subplot(2,4,4)
    plt.imshow(fourth_order)
    plt.colorbar()
    plt.subplot(2,4,5)
    plt.imshow(fifth_order)
    plt.colorbar()
    plt.subplot(2,4,6)
    plt.imshow(sixth_order)
    plt.colorbar()
    plt.subplot(2,4,7)
    plt.imshow(seventh_order)
    plt.colorbar()
    plt.show(block=False)

    plt.figure()
    plt.imshow(lamb)
    plt.colorbar()
    plt.show(block=False)

    plt.figure()
    plt.imshow(field)
    plt.colorbar()
    plt.show()
