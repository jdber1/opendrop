#ifndef OPENDROP_INTERPOLATE_HPP
#define OPENDROP_INTERPOLATE_HPP

#include <array>
#include <cstddef>
#include <vector>


namespace opendrop {
namespace interpolate {


template <typename Real, std::size_t N>
class HermiteQuinticSplineND {
public:
    std::pair<Real, Real> domain();

    template <typename InputIt1, typename InputIt2, typename InputIt3>
    void push_back(Real t, InputIt1 y_it, InputIt2 v_it, InputIt3 a_it);

    template <typename T>
    auto operator()(T t);

private:
    inline void check_domain(Real t);

    std::vector<Real> t_breaks;
    std::vector<std::array<Real, N>> y_breaks;
    std::vector<std::array<Real, N>> v_breaks;
    std::vector<std::array<Real, N>> a_breaks;
};


template <typename Real>
class LinearSpline1D {
public:
    std::pair<Real, Real> domain();

    void push_back(Real t, Real y);

    template <typename T>
    auto operator()(T t);

private:
    inline void check_domain(Real t);

    std::vector<Real> t_breaks;
    std::vector<Real> y_breaks;
    std::vector<Real> slopes;
};


}  // namespace interpolate
}  // namespace opendrop


#include <opendrop/interpolate_detail.hpp>

#endif
