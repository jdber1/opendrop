#ifndef OPENDROP_INTERPOLATE_DETAIL_HPP
#define OPENDROP_INTERPOLATE_DETAIL_HPP

#include <algorithm>
#include <array>
#include <cstddef>
#include <stdexcept>
#include <sstream>
#include <utility>
#include <vector>

#include <boost/math/differentiation/autodiff.hpp>
#include <opendrop/interpolate.hpp>


namespace opendrop {
namespace interpolate {


namespace detail {
    using namespace boost::math::differentiation;
}


template <typename Real, std::size_t N>
std::pair<Real, Real>
HermiteQuinticSplineND<Real, N>::domain()
{
    return {t_breaks.front(), t_breaks.back()};
}


template <typename Real, std::size_t N>
template <typename InputIt1, typename InputIt2, typename InputIt3>
void
HermiteQuinticSplineND<Real, N>::push_back(Real t, InputIt1 y_it, InputIt2 v_it, InputIt3 a_it)
{
    std::array<Real, N> y, v, a;
    std::copy_n(y_it, N, y.begin());
    std::copy_n(v_it, N, v.begin());
    std::copy_n(a_it, N, a.begin());

    t_breaks.push_back(t);
    y_breaks.push_back(std::move(y));
    v_breaks.push_back(std::move(v));
    a_breaks.push_back(std::move(a));
}


template <typename Real, std::size_t N>
template <typename T>
auto
HermiteQuinticSplineND<Real, N>::operator()(T t) {
    check_domain(static_cast<Real>(t));

    std::array<detail::promote<Real, T>, N> result;

    if (t_breaks.size() == 1) {
        Real &t0 = t_breaks[0];
        auto &y0 = y_breaks[0];
        auto &v0 = v_breaks[0];
        auto &a0 = a_breaks[0];

        auto epsilon = t - t0;

        for (size_t j = 0; j < N; j++) {
            result[j] = y0[j] + epsilon*v0[j] + 0.5*epsilon*epsilon*a0[j];
        }

        return result;
    }

    size_t i;
    if (static_cast<Real>(t) == t_breaks.back()) {
        i = t_breaks.size() - 1;
    } else {
        i = std::distance(
            t_breaks.begin(),
            std::upper_bound(t_breaks.begin(), t_breaks.end(), static_cast<Real>(t))
        );
    }

    Real &t0 = t_breaks[i-1];
    Real &t1 = t_breaks[i];
    Real dt = t1 - t0;

    auto x = (t - t0)/dt;
    auto x2 = x*x;
    auto x3 = x2*x;

    auto &y0 = y_breaks[i-1];
    auto &y1 = y_breaks[i];
    auto &v0 = v_breaks[i-1];
    auto &v1 = v_breaks[i];
    auto &a0 = a_breaks[i-1];
    auto &a1 = a_breaks[i];

    for (size_t j = 0; j < N; j++) {
        result[j] = (
            (1 - x3*(10 + x*(-15 + 6*x)))*y0[j]
            + x*(1 + x2*(-6 + x*(8 -3*x)))*dt*v0[j]
            + x2*(1 + x*(-3 + x*(3-x)))*dt*dt/2*a0[j]
            + x3*(
                (1 + x*(-2 + x))*dt*dt/2*a1[j]
                + (-4 + x*(7 - 3*x))*dt*v1[j]
                + (10 + x*(-15 + 6*x))*y1[j]
            )
        );
    }

    return result;
}


template <typename Real, std::size_t N>
inline void
HermiteQuinticSplineND<Real, N>::check_domain(Real t)
{
    if (t_breaks.size() < 1) {
        throw std::runtime_error("Spline is empty");
    }

    if (t < t_breaks.front() || t > t_breaks.back()) {
        std::ostringstream oss;
        oss.precision(std::numeric_limits<Real>::digits10+3);
        oss << "Requested t = " << t << ", which is outside of the interpolation domain ["
            << t_breaks.front() << ", " << t_breaks.back() << "]";
        throw std::domain_error(oss.str());
    }
}


template <typename Real>
std::pair<Real, Real>
LinearSpline1D<Real>::domain()
{
    return {t_breaks.front(), t_breaks.back()};
}


template <typename Real>
void
LinearSpline1D<Real>::push_back(Real t, Real y)
{
    t_breaks.push_back(t);
    y_breaks.push_back(y);
    
    size_t i = y_breaks.size() - 1;
    if (i > 0) {
        slopes.push_back((y_breaks[i] - y_breaks[i-1])/(t_breaks[i] - t_breaks[i-1]));
    }
}


template <typename Real>
template <typename T>
auto
LinearSpline1D<Real>::operator()(T t) {
    check_domain(static_cast<Real>(t));

    if (t_breaks.size() == 1) {
        return y_breaks[0] + t*0;
    }

    size_t i;
    if (static_cast<Real>(t) == t_breaks.back()) {
        i = t_breaks.size() - 1;
    } else {
        i = std::distance(
            t_breaks.begin(),
            std::upper_bound(t_breaks.begin(), t_breaks.end(), t)
        );
    }

    Real &t0 = t_breaks[i-1];
    Real &y0 = y_breaks[i-1];
    Real &slope = slopes[i-1];

    return y0 + slope*(t - t0);
}


template <typename Real>
inline void
LinearSpline1D<Real>::check_domain(Real t) {
    if (t_breaks.size() < 1) {
        throw std::runtime_error("Spline is empty");
    }

    if (t < t_breaks.front() || t > t_breaks.back()) {
        std::ostringstream oss;
        oss.precision(std::numeric_limits<Real>::digits10+3);
        oss << "Requested t = " << t << ", which is outside of the interpolation domain ["
            << t_breaks.front() << ", " << t_breaks.back() << "]";
        throw std::domain_error(oss.str());
    }
}


}  // namespace interpolate
}  // namespace opendrop

#endif
