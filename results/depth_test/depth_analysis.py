import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    x = np.array([0, 10, 20, 30, 40, 50])

    white_red = np.array([0.815, 0.946, 1.094, 1.350, 1.438, 1.460])
    white_nir = np.array([0.795, 0.887, 1.006, 1.194, 1.376, 1.425])
    foil_red = np.array([0.833, 0.896, 1.063, 1.170, 1.280, 1.305])
    foil_nir = np.array([0.805, 0.881, 1.017, 1.171, 1.396, 1.748])

    white_rel_dif = np.divide(white_red, white_nir)
    foil_rel_dif = np.divide(foil_red, foil_nir)

    plt.figure()
    plt.plot(x, white_red, 'ro')
    plt.plot(x, white_nir, 'bo')
    plt.plot(x, white_rel_dif, 'c')
    plt.xlabel("Dist. from ground [cm]")
    plt.ylabel("Reflection coeff. [-]")
    plt.legend(["Red reflectivity", "Nir reflectivity", "Relative (red/nir)"])
    plt.title("Diffuse white paper")
    plt.show(block=False)

    plt.figure()
    plt.plot(x, foil_red, 'ro')
    plt.plot(x, foil_nir, 'bo')
    plt.plot(x, foil_rel_dif, 'c')
    plt.xlabel("Dist. from ground [cm]")
    plt.ylabel("Reflection coeff. [-]")
    plt.legend(["Red reflectivity", "Nir reflectivity", "Relative (red/nir)"])
    plt.title("Reflective foil")
    plt.show(block=False)

    h = np.linspace(3, 63, num=20)
    sim_fo = np.array([0.99971818, 0.9957733, 0.98381572, 0.96607889, 0.94753302, 0.93036165, 0.91469072, 0.90010034, 0.88621538, 0.87281935, 0.85981809, 0.84718137, 0.83490201, 0.82297637, 0.81139808, 0.80015788, 0.78924493, 0.7786481, 0.76835676, 0.75836105])

    plt.figure()
    plt.plot(x, white_rel_dif, 'c')
    plt.plot(x, foil_rel_dif, 'k')
    plt.plot(x, np.divide(foil_rel_dif, white_rel_dif), 'm')
    plt.plot(h, sim_fo, 'r')
    plt.xlabel("Dist. from ground [cm]")
    plt.ylabel("Relative diff [-]")
    plt.legend(["White paper relative (red/nir)", "Foil relative (red/nir)", "Measured diff (white/foil)", "Simulated diff (white/foil)"])
    plt.title("Measured vs simulated intensity falloff")
    plt.show()
