#define BOOST_TEST_MODULE TestInterpolate
#include <boost/test/unit_test.hpp>

#include <array>
#include <opendrop/interpolate.hpp>
#include <boost/math/differentiation/autodiff.hpp>
#include <boost/numeric/ublas/vector.hpp>
#include <boost/numeric/ublas/assignment.hpp>
#include <boost/numeric/ublas/io.hpp>

using namespace opendrop::interpolate;
namespace tt = boost::test_tools;


BOOST_AUTO_TEST_CASE(test_hermite_quintic_spline_push_back)
{
    HermiteQuinticSplineND<double, 1> spline;

    int t = 1;
    int y = 2;
    int v = 2;
    int a = 3;

    spline.push_back(t, &y, &v, &a);
}


BOOST_AUTO_TEST_CASE(test_hermite_quintic_spline_empty)
{
    HermiteQuinticSplineND<double, 1> spline;

    BOOST_CHECK_THROW(spline(0), std::runtime_error);

    int x = 1;
    spline.push_back(x, &x, &x, &x);

    spline(1);
}


BOOST_AUTO_TEST_CASE(test_hermite_quintic_spline_single_breakpoint)
{
    using namespace boost::math::differentiation;

    HermiteQuinticSplineND<double, 1> spline;

    BOOST_CHECK_THROW(spline(0), std::runtime_error);

    double t = 1.0;
    double y = 2.0;
    double v = 3.0;
    double a = 4.0;
    spline.push_back(t, &y, &v, &a);

    auto f = spline(make_fvar<double, 4>(t));
    BOOST_TEST(f[0].derivative(0) == y);
    BOOST_TEST(f[0].derivative(1) == v);
    BOOST_TEST(f[0].derivative(2) == a);
    BOOST_TEST(f[0].derivative(3) == 0);
}


BOOST_AUTO_TEST_CASE(test_hermite_quintic_spline_call)
{
    HermiteQuinticSplineND<double, 1> spline;

    double t, y, v, a;
    t = 0.0;
    y = 0.0;
    v = 1.0;
    a = 0.0;
    spline.push_back(t, &y, &v, &a);
    t = 1.0;
    y = 0.841470984808;
    v = 0.540302305868;
    a = -0.841470984808;
    spline.push_back(t, &y, &v, &a);

    BOOST_TEST(spline(0.5)[0] == 0.479415, tt::tolerance(1e-6));
}


BOOST_AUTO_TEST_CASE(test_hermite_quintic_spline_call_with_fvar)
{
    using namespace boost::math::differentiation;

    HermiteQuinticSplineND<double, 1> spline;

    double t, y, v, a;
    t = 0.0;
    y = 0.0;
    v = 1.0;
    a = 0.0;
    spline.push_back(t, &y, &v, &a);
    t = 1.0;
    y = 0.841470984808;
    v = 0.540302305868;
    a = -0.841470984808;
    spline.push_back(t, &y, &v, &a);

    auto f = spline(make_fvar<double, 2>(0.5));

    BOOST_CHECK(f[0].order_sum == 2);
    BOOST_TEST(f[0].derivative(0) == 0.479415, tt::tolerance(1e-6));
    BOOST_TEST(f[0].derivative(1) == 0.877580, tt::tolerance(1e-6));
    BOOST_TEST(f[0].derivative(2) == -0.479179, tt::tolerance(1e-6));
}


BOOST_AUTO_TEST_CASE(test_hermite_quintic_spline_with_vector)
{
    using namespace boost::math::differentiation;

    HermiteQuinticSplineND<double, 2> spline;

    double t, y[2], a[2], v[2];
    t = 0.0;
    y[0] = 0.0;
    y[1] = 1.0;
    a[0] = 1.0;
    a[1] = 0.0;
    v[0] = 0.0;
    v[1] = -1.0;
    spline.push_back(t, y, a, v);
    t = 1.0;
    y[0] = 0.841470984808;
    y[1] = 0.540302305868;
    a[0] = 0.540302305868;
    a[1] = -0.841470984808;
    v[0] = -0.841470984808;
    v[1] = -0.540302305868;
    spline.push_back(t, y, a, v);

    auto f1 = spline(0.5);
    BOOST_TEST(f1[0] == 0.479415, tt::tolerance(1e-6));
    BOOST_TEST(f1[1] == 0.877564, tt::tolerance(1e-6));

    auto f2 = spline(make_fvar<double, 2>(0.5));
    BOOST_TEST(f2[0].derivative(0) == 0.479415, tt::tolerance(1e-6));
    BOOST_TEST(f2[1].derivative(0) == 0.877564, tt::tolerance(1e-6));
    BOOST_TEST(f2[0].derivative(1) == 0.877580, tt::tolerance(1e-6));
    BOOST_TEST(f2[1].derivative(1) == -0.479424, tt::tolerance(1e-6));
    BOOST_TEST(f2[0].derivative(2) == -0.479179, tt::tolerance(1e-6));
    BOOST_TEST(f2[1].derivative(2) == -0.877131, tt::tolerance(1e-6));
}


BOOST_AUTO_TEST_CASE(test_linear_spline_1d_push_back)
{
    LinearSpline1D<double> spline;

    spline.push_back(1, 2);
}


BOOST_AUTO_TEST_CASE(test_linear_spline_1d_empty)
{
    LinearSpline1D<double> spline;

    BOOST_CHECK_THROW(spline(0), std::runtime_error);

    spline.push_back(1, 2);

    spline(1);
}


BOOST_AUTO_TEST_CASE(test_linear_spline_1d_single_breakpoint)
{
    using namespace boost::math::differentiation;

    LinearSpline1D<double> spline;

    BOOST_CHECK_THROW(spline(0), std::runtime_error);

    double t = 1.0;
    double y = 2.0;
    spline.push_back(t, y);

    auto f = spline(make_fvar<double, 2>(t));
    BOOST_TEST(f.derivative(0) == y);
    BOOST_TEST(f.derivative(1) == 0);
}


BOOST_AUTO_TEST_CASE(test_linear_spline_1d_call)
{
    LinearSpline1D<double> spline;

    spline.push_back(0.0, 0.0);
    spline.push_back(1.0, 1.0);

    BOOST_TEST(spline(0.5) == 0.5);
}


BOOST_AUTO_TEST_CASE(test_linear_spline_1d_call_with_fvar)
{
    using namespace boost::math::differentiation;

    LinearSpline1D<double> spline;

    spline.push_back(0.0, 0.0);
    spline.push_back(1.0, 1.0);

    auto f = spline(make_fvar<double, 2>(0.5));

    BOOST_CHECK(f.order_sum == 2);
    BOOST_TEST(f.derivative(0) == 0.5);
    BOOST_TEST(f.derivative(1) == 1.0);
    BOOST_TEST(f.derivative(2) == 0.0);
}
