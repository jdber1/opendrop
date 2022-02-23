#define BOOST_TEST_MODULE TestYoungLaplace
#include <boost/test/unit_test.hpp>

#include <array>

#include <opendrop/younglaplace.hpp>

using namespace opendrop::younglaplace;
namespace tt = boost::test_tools;


BOOST_AUTO_TEST_CASE(test_young_laplace_shape_call)
{
    YoungLaplaceShape<double> shape(0.21);

    double s[] = {-0.2, -0.1, 0.0, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2};

    double r[] = {
        -1.98671000e-1,
        -9.98334690e-2,
        0.00000000e+0,
        9.98334690e-2,
        1.98671000e-1,
        3.89470759e-1,
        7.18911827e-1,
        1.03671685e+0, 
        3.53242294e-1,
    };

    double z[] = {
        1.99230742e-2,
        4.99518094e-3,
        0.00000000e+0,
        4.99518094e-3,
        1.99230742e-2,
        7.87805625e-2,
        3.01185635e-1,
        1.01682486e+0,
        2.40649189e+0,
    };

    for (size_t i = 0; i < sizeof(s)/sizeof(*s); i++) {
        auto x = shape(s[i]);
        BOOST_TEST(x[0] == r[i], tt::tolerance(1e-3));
        BOOST_TEST(x[1] == z[i], tt::tolerance(1e-3));
    }
}


BOOST_AUTO_TEST_CASE(test_young_laplace_shape_copy_constructor)
{
    YoungLaplaceShape<double> shape1(0.123);

    // Do some calculations to populate its cache.
    shape1(0.5);

    // Copy constructor;
    YoungLaplaceShape<double> shape2 = shape1;

    for (int i = 0; i < 10; i++) {
        auto x1 = shape1(i/10.0);
        auto x2 = shape2(i/10.0);
        BOOST_TEST(x1[0] == x2[0]);
        BOOST_TEST(x1[1] == x2[1]);
    }
}


BOOST_AUTO_TEST_CASE(test_young_laplace_shape_copy_assignment)
{
    YoungLaplaceShape<double> shape1(0.123);
    YoungLaplaceShape<double> shape2(0.456);

    // Do some calculations to populate their cache.
    shape1(0.5);
    shape2(0.5);

    // Copy assignment.
    shape1 = shape2;

    for (int i = 0; i < 10; i++) {
        auto x1 = shape1(i/10.0);
        auto x2 = shape2(i/10.0);
        BOOST_TEST(x1[0] == x2[0]);
        BOOST_TEST(x1[1] == x2[1]);
    }
}


BOOST_AUTO_TEST_CASE(test_young_laplace_zinv)
{
    YoungLaplaceShape<double> shape(0.21);

    double s[] = {0.0, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2};

    double z[] = {
        0.00000000e+0,
        4.99518094e-3,
        1.99230742e-2,
        7.87805625e-2,
        3.01185635e-1,
        1.01682486e+0,
        2.40649189e+0,
    };

    for (size_t i = 0; i < sizeof(s)/sizeof(*s); i++) {
        // z_inv() uses linear interpolation so is not very precise.
        BOOST_TEST(shape.z_inv(z[i]) == s[i], tt::tolerance(5e-2));
    }
}


BOOST_AUTO_TEST_CASE(test_young_laplace_zinv_outside_domain)
{
    YoungLaplaceShape<double> shape(0.21);

    BOOST_CHECK_THROW(shape.z_inv(-1), std::domain_error);
    BOOST_CHECK_THROW(shape.z_inv(100000), std::domain_error);
}


BOOST_AUTO_TEST_CASE(test_young_laplace_closest)
{
    using namespace boost::math::differentiation;

    YoungLaplaceShape<double> shape(0.21);

    BOOST_TEST(shape.closest(0.73, 0.27) == 0.786139, tt::tolerance(1e-5));
    BOOST_TEST(shape.closest(0.0, -1.0) == 0.0, tt::tolerance(1e-10));
}


BOOST_AUTO_TEST_CASE(test_young_laplace_volume)
{
    YoungLaplaceShape<double> shape(0.21);

    BOOST_TEST(shape.volume(4.0) == 5.53648, tt::tolerance(1e-3));
}


BOOST_AUTO_TEST_CASE(test_young_laplace_surface_area)
{
    YoungLaplaceShape<double> shape(0.21);

    BOOST_TEST(shape.surface_area(4.0) == 15.9890, tt::tolerance(1e-3));
}
