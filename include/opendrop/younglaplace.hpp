#ifndef YOUNG_LAPLACE_HPP
#define YOUNG_LAPLACE_HPP

#include <cstddef>
#include <algorithm>
#include <limits>
#include <utility>

#include <arkode/arkode_erkstep.h>
#include <nvector/nvector_serial.h>

#include <boost/concept/requires.hpp>
#include <boost/concept_check.hpp>
#include <boost/math/differentiation/autodiff.hpp>
#include <boost/numeric/ublas/vector.hpp>

#include <opendrop/interpolate.hpp>


namespace opendrop {
namespace younglaplace {


namespace detail {

using namespace opendrop::interpolate;

using sunreal = realtype;
template <typename T, std::size_t N>
using fvar = boost::math::differentiation::detail::fvar<T, N>;

}


template <typename realtype>
class YoungLaplaceShape {
    static constexpr realtype RTOL = 1.e-4;
    static constexpr realtype ATOL = 1.e-9;
    static constexpr realtype MAX_ARCLENGTH = 100.0;

    static constexpr realtype CLOSEST_TOL = 1.e-6;
    static constexpr size_t MAX_CLOSEST_ITER = 10;

public:
    realtype bond;

    YoungLaplaceShape(realtype bond);

    YoungLaplaceShape();

    YoungLaplaceShape(const YoungLaplaceShape<realtype> &other);

    YoungLaplaceShape<realtype> & operator=(const YoungLaplaceShape<realtype> &other);

    ~YoungLaplaceShape();

    template <typename T>
    auto operator()(T s);

    template <typename T>
    auto DBo(T s);

    template <typename T>
    auto z_inv(T z);

    realtype closest(realtype r, realtype z);

    realtype volume(realtype s);

    realtype surface_area(realtype s);

private:
    detail::HermiteQuinticSplineND<realtype, 2> dense;
    detail::HermiteQuinticSplineND<realtype, 2> dense_DBo;
    detail::LinearSpline1D<realtype> dense_z_inv;
    bool max_z_solved = false;

    void *arkode_mem;
    N_Vector nv;

    void *arkode_mem_DBo;
    N_Vector nv_DBo;

    template <typename T>
    inline void
    check_domain(T s);

    template <typename T, typename RandomAccessIt1, typename RandomAccessIt2, typename OutputIt>
    static void
    ode(YoungLaplaceShape<realtype> *self,
        const T &s,
        const RandomAccessIt1 y,
        const RandomAccessIt2 dy_ds,
        OutputIt d2y_ds2);

    template <typename T, typename RandomAccessIt1, typename RandomAccessIt2, typename OutputIt>
    static void
    ode_DBo(YoungLaplaceShape<realtype> *self,
            const T &s,
            const RandomAccessIt1 y,
            const RandomAccessIt2 dy_ds,
            OutputIt d2y_ds2);

    template <typename T, typename RandomAccessIt, typename OutputIt>
    static void
    ode_vol(YoungLaplaceShape<realtype> *self,
            const T &s,
            const RandomAccessIt y,
            OutputIt dy_ds);

    template <typename T, typename RandomAccessIt, typename OutputIt>
    static void
    ode_surf(YoungLaplaceShape<realtype> *self,
             const T &s,
             const RandomAccessIt y,
             OutputIt dy_ds);

    static int arkrhs(detail::sunreal s, const N_Vector nv, N_Vector nvdot, void *user_data);

    static int arkrhs_DBo(detail::sunreal s, const N_Vector nv, N_Vector nvdot, void *user_data);

    static int arkrhs_vol(detail::sunreal s, const N_Vector nv, N_Vector nvdot, void *user_data);

    static int arkrhs_surf(detail::sunreal s, const N_Vector nv, N_Vector nvdot, void *user_data);

    static int arkroot(detail::sunreal s, const N_Vector nv, detail::sunreal *out, void *user_data);

    void step();

    void step_DBo();
};


}  // namespace younglaplace
}  // namespace opendrop


#include <opendrop/younglaplace_detail.hpp>

#endif
