#ifndef OPENDROP_YOUNG_LAPLACE_DETAIL_HPP
#define OPENDROP_YOUNG_LAPLACE_DETAIL_HPP

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <utility>

#include <arkode/arkode_erkstep.h>
#include <nvector/nvector_serial.h>
#include <boost/math/differentiation/autodiff.hpp>
#include <boost/math/constants/constants.hpp>

#include <opendrop/interpolate.hpp>
#include <opendrop/younglaplace.hpp>


namespace opendrop {
namespace younglaplace {


namespace detail {

using namespace opendrop::interpolate;

using sunreal = realtype;
template <typename T, std::size_t N>
using fvar = boost::math::differentiation::detail::fvar<T, N>;

}


template <typename realtype>
constexpr realtype YoungLaplaceShape<realtype>::RTOL;
template <typename realtype>
constexpr realtype YoungLaplaceShape<realtype>::ATOL;
template <typename realtype>
constexpr realtype YoungLaplaceShape<realtype>::MAX_ARCLENGTH;
template <typename realtype>
constexpr realtype YoungLaplaceShape<realtype>::CLOSEST_TOL;
template <typename realtype>
constexpr size_t YoungLaplaceShape<realtype>::MAX_CLOSEST_ITER;


template <typename realtype>
YoungLaplaceShape<realtype>::YoungLaplaceShape(realtype bond) {
    int flag;

    this->bond = bond;

    nv = N_VNew_Serial(4);
    if (nv == NULL) throw std::runtime_error("N_VNew_Serial() failed.");
    nv_DBo = N_VNew_Serial(4);
    if (nv_DBo == NULL) throw std::runtime_error("N_VNew_Serial() failed.");

    // Initial conditions.
    NV_Ith_S(nv, 0) = RCONST(0.0);  // r
    NV_Ith_S(nv, 1) = RCONST(0.0);  // z
    NV_Ith_S(nv, 2) = RCONST(1.0);  // dr/ds
    NV_Ith_S(nv, 3) = RCONST(0.0);  // dz/ds

    NV_Ith_S(nv_DBo, 0) = RCONST(0.0);  // dr/dBo
    NV_Ith_S(nv_DBo, 1) = RCONST(0.0);  // dz/dBo
    NV_Ith_S(nv_DBo, 2) = RCONST(0.0);  // d2r/dBods
    NV_Ith_S(nv_DBo, 3) = RCONST(0.0);  // d2z/dBods

    realtype a0[] = {0.0, 1.0};  // (d2r/ds2, d2z/ds2)
    dense.push_back(0.0, NV_DATA_S(nv), NV_DATA_S(nv) + 2, a0);

    realtype a0_DBo[] = {0.0, 0.0};  // (d3r/dBods2, d3z/dBods2)
    dense_DBo.push_back(0.0, NV_DATA_S(nv_DBo), NV_DATA_S(nv_DBo) + 2, a0_DBo);

    dense_z_inv.push_back(0.0, 0.0);

    arkode_mem = ERKStepCreate(arkrhs, RCONST(0.0), nv);
    if (arkode_mem == NULL) throw std::runtime_error("ERKStepCreate() failed.");

    flag = ERKStepRootInit(arkode_mem, 1, arkroot);
    if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepRootInit() failed.");

    flag = ERKStepSetUserData(arkode_mem, (void *) this);
    if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepSetUserData() failed.");

    flag = ERKStepSetTableNum(arkode_mem, DEFAULT_ERK_6);
    if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepSetTableNum() failed.");

    flag = ERKStepSStolerances(arkode_mem, RTOL, ATOL);
    if (flag == ARK_ILL_INPUT) throw std::domain_error("ERKStepSStolerances() returned ARK_ILL_INPUT.");
    else if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepSStolerances() failed.");

    arkode_mem_DBo = ERKStepCreate(arkrhs_DBo, RCONST(0.0), nv_DBo);
    if (arkode_mem_DBo == NULL) throw std::runtime_error("ERKStepCreate() failed.");

    flag = ERKStepSetUserData(arkode_mem_DBo, (void *) this);
    if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepSetUserData() failed.");

    flag = ERKStepSetTableNum(arkode_mem_DBo, DEFAULT_ERK_6);
    if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepSetTableNum() failed.");

    flag = ERKStepSStolerances(arkode_mem_DBo, RTOL, ATOL);
    if (flag == ARK_ILL_INPUT) throw std::domain_error("ERKStepSStolerances() returned ARK_ILL_INPUT.");
    else if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepSStolerances() failed.");
}


template <typename realtype>
YoungLaplaceShape<realtype>::YoungLaplaceShape() : YoungLaplaceShape(0.0) {}


template <typename realtype>
YoungLaplaceShape<realtype>::YoungLaplaceShape(const YoungLaplaceShape<realtype> &other)
    : YoungLaplaceShape(other.bond)
{
    // Reuse cached results.
    dense = other.dense;
    dense_DBo = other.dense_DBo;
    max_z_solved = other.max_z_solved;
}


template <typename realtype>
YoungLaplaceShape<realtype>::~YoungLaplaceShape() {
    ERKStepFree(&arkode_mem);
    ERKStepFree(&arkode_mem_DBo);
    N_VDestroy(nv);
    N_VDestroy(nv_DBo);
}


template <typename realtype>
YoungLaplaceShape<realtype> &
YoungLaplaceShape<realtype>::operator=(const YoungLaplaceShape<realtype> &other)
{
    int flag;

    bond = other.bond;

    // Reuse cached results.
    dense = other.dense;
    dense_DBo = other.dense_DBo;
    max_z_solved = other.max_z_solved;

    // Initial conditions.
    NV_Ith_S(nv, 0) = RCONST(0.0);  // r
    NV_Ith_S(nv, 1) = RCONST(0.0);  // z
    NV_Ith_S(nv, 2) = RCONST(1.0);  // dr/ds
    NV_Ith_S(nv, 3) = RCONST(0.0);  // dz/ds

    NV_Ith_S(nv_DBo, 0) = RCONST(0.0);  // dr/dBo
    NV_Ith_S(nv_DBo, 1) = RCONST(0.0);  // dz/dBo
    NV_Ith_S(nv_DBo, 2) = RCONST(0.0);  // d2r/dBods
    NV_Ith_S(nv_DBo, 3) = RCONST(0.0);  // d2z/dBods

    flag = ERKStepReInit(arkode_mem, arkrhs, RCONST(0.0), nv);
    if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepReInit() failed.");
    flag = ERKStepReInit(arkode_mem_DBo, arkrhs_DBo, RCONST(0.0), nv_DBo);
    if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepReInit() failed.");

    if (max_z_solved) flag = ERKStepRootInit(arkode_mem, 0, NULL);
                 else flag = ERKStepRootInit(arkode_mem, 1, arkroot);
    if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepRootInit() failed.");

    return *this;
}


template <typename realtype>
template <typename T>
auto
YoungLaplaceShape<realtype>::operator()(T s)
{
    using namespace boost::math::differentiation;

    check_domain(s);

    T s_abs;

    // XXX: Do not use boost::math::differentiation::abs since it sets derivative at s=0 to 0 which causes
    // problems with closest().
    if (s >= 0.0) {
        s_abs = s;
    } else {
        s_abs = -s;
    }

    // Be careful this doesn't cause an infinite loop when working with NaNs.
    while (std::get<1>(dense.domain()) < std::min(static_cast<realtype>(s_abs), MAX_ARCLENGTH)) {
        step();
    }

    auto ans = dense(s_abs);

    // Flip sign of r if s < 0.
    if (s < 0) ans[0] *= -1;

    return ans;
}


template <typename realtype>
template <typename T>
auto
YoungLaplaceShape<realtype>::DBo(T s)
{
    using namespace boost::math::differentiation;

    check_domain(s);

    T s_abs = abs(s);

    // Be careful this doesn't cause an infinite loop when working with NaNs.
    while (std::get<1>(dense_DBo.domain()) < std::min(static_cast<realtype>(s_abs), MAX_ARCLENGTH)) {
        step_DBo();
    }

    auto ans = dense_DBo(s_abs);

    // Flip sign of dr/dBo if s < 0.
    if (s < 0) ans[0] *= -1;

    return ans;
}


template <typename realtype>
template <typename T>
inline void
YoungLaplaceShape<realtype>::check_domain(T s)
{
    if (s < -MAX_ARCLENGTH || s > MAX_ARCLENGTH) {
        std::ostringstream oss;
        oss.precision(std::numeric_limits<realtype>::digits10+3);
        oss << "Requested s = " << static_cast<realtype>(s) << ", which is outside of the solution domain ["
            << -MAX_ARCLENGTH << ", " << MAX_ARCLENGTH << "]";
        throw std::domain_error(oss.str());
    }
}


template <typename realtype>
template <typename T>
auto
YoungLaplaceShape<realtype>::z_inv(T z) {
    // Be careful this doesn't cause an infinite loop when working with NaNs.
    while (std::get<1>(dense_z_inv.domain()) < static_cast<realtype>(z) && !max_z_solved) {
        step();
    }

    auto domain = dense_z_inv.domain();
    if (z < std::get<0>(domain) || z > std::get<1>(domain)) {
        std::ostringstream oss;
        oss.precision(std::numeric_limits<realtype>::digits10+3);
        oss << "Requested z = " << static_cast<realtype>(z) << ", which is outside of the one-to-one domain ["
            << std::get<0>(domain) << ", ";

        if (max_z_solved) oss << std::get<1>(domain) << "]";
                     else oss << "?]";

        throw std::domain_error(oss.str());
    }

    return dense_z_inv(z);
}


template <typename realtype>
realtype
YoungLaplaceShape<realtype>::closest(realtype r, realtype z) {
    using namespace boost::math::differentiation;

    realtype s_prev, s;

    // Set initial guess to point with height equal to z.
    if (z > 0) {
        try { 
            s = z_inv(z);
        } catch (std::domain_error &) {
            // z is too high, set guess to max s (corresponding to max z).
            s = MAX_ARCLENGTH;
        }
    } else {
        s = 0.0;
    }

    if (r < 0) {
        s *= -1;
    }

    for (size_t i = 0; i < MAX_CLOSEST_ITER; i++) {
        s_prev = s;

        auto predict = (*this)(make_fvar<realtype, 2>(s));

        auto e_r = r - predict[0];
        auto e_z = z - predict[1];
        auto e2 = e_r*e_r + e_z*e_z;

        s = s - e2.derivative(1)/std::abs(e2.derivative(2));

        // Restrict s within solution domain.
        if (s > MAX_ARCLENGTH) {
            s = MAX_ARCLENGTH;
        } else if (s < -MAX_ARCLENGTH) {
            s = -MAX_ARCLENGTH;
        }

        if (std::abs(s - s_prev) < CLOSEST_TOL) break;
    }
    
    return s;
}


template <typename realtype>
realtype
YoungLaplaceShape<realtype>::volume(realtype s)
{
    check_domain(s);

    int flag;
    detail::sunreal data[] = {RCONST(0.0)};

    s = std::abs(s);

    N_Vector nv_vol = N_VMake_Serial(1, data);
    if (nv_vol == NULL) throw std::runtime_error("N_VMake_Serial() failed.");

    void *arkode_mem_vol = ERKStepCreate(arkrhs_vol, RCONST(0.0), nv_vol);
    if (arkode_mem_vol == NULL) throw std::runtime_error("ERKStepCreate() failed.");

    flag = ERKStepSetUserData(arkode_mem_vol, (void *) this);
    if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepSetUserData() failed.");

    flag = ERKStepSStolerances(arkode_mem_vol, RTOL, ATOL);
    if (flag == ARK_ILL_INPUT) throw std::domain_error("ERKStepSStolerances() returned ARK_ILL_INPUT.");
    else if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepSStolerances() failed.");

    flag = ERKStepSetStopTime(arkode_mem_vol, s);
    if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepSetStopTime() failed.");

    flag = ERKStepEvolve(arkode_mem_vol, s, nv_vol, &s, ARK_NORMAL);
    if (flag < 0) throw std::runtime_error("ERKStepEvolve() failed.");

    ERKStepFree(&arkode_mem_vol);
    N_VDestroy(nv_vol);

    return data[0];
}


template <typename realtype>
realtype
YoungLaplaceShape<realtype>::surface_area(realtype s)
{
    check_domain(s);

    int flag;
    detail::sunreal data[] = {RCONST(0.0)};

    s = std::abs(s);

    N_Vector nv_surf = N_VMake_Serial(1, data);
    if (nv_surf == NULL) throw std::runtime_error("N_VMake_Serial() failed.");

    void *arkode_mem_surf = ERKStepCreate(arkrhs_surf, RCONST(0.0), nv_surf);
    if (arkode_mem_surf == NULL) throw std::runtime_error("ERKStepCreate() failed.");

    flag = ERKStepSetUserData(arkode_mem_surf, (void *) this);
    if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepSetUserData() failed.");

    flag = ERKStepSStolerances(arkode_mem_surf, RTOL, ATOL);
    if (flag == ARK_ILL_INPUT) throw std::domain_error("ERKStepSStolerances() returned ARK_ILL_INPUT.");
    else if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepSStolerances() failed.");

    flag = ERKStepSetStopTime(arkode_mem_surf, s);
    if (flag != ARK_SUCCESS) throw std::runtime_error("ERKStepSetStopTime() failed.");

    flag = ERKStepEvolve(arkode_mem_surf, s, nv_surf, &s, ARK_NORMAL);
    if (flag < 0) throw std::runtime_error("ERKStepEvolve() failed.");

    ERKStepFree(&arkode_mem_surf);
    N_VDestroy(nv_surf);

    return data[0];
}


template <typename realtype>
void
YoungLaplaceShape<realtype>::step()
{
    int flag;
    detail::sunreal tcur, tnext;
    realtype y[2], dy_ds[2], d2y_ds2[2];

    flag = ERKStepGetCurrentTime(arkode_mem, &tcur);
    if (flag == ARK_MEM_NULL) throw std::runtime_error("ARK_MEM_NULL");

    if (tcur == RCONST(0.0)) {
        // First step. Set tout to 0.1 to give a rough scale of t variable when using ARK_ONE_STEP.
        tnext = tcur + RCONST(0.1);
    } else {
        tnext = std::numeric_limits<detail::sunreal>::infinity();
    }

    flag = ERKStepEvolve(arkode_mem, tnext, nv, &tcur, ARK_ONE_STEP);
    if (flag < 0) throw std::runtime_error("ERKStepEvolve() failed.");

    const bool max_z_just_solved = (flag == ARK_ROOT_RETURN);

    y[0] = NV_Ith_S(nv, 0);
    y[1] = NV_Ith_S(nv, 1);
    dy_ds[0] = NV_Ith_S(nv, 2);
    dy_ds[1] = NV_Ith_S(nv, 3);

    ode(this, tcur, y, dy_ds, d2y_ds2);

    dense.push_back(tcur, y, dy_ds, d2y_ds2);

    if (!max_z_solved) {
        dense_z_inv.push_back(y[1], tcur);
        if (max_z_just_solved) {
            // Stop checking for dz_ds = 0.
            ERKStepRootInit(arkode_mem, 0, NULL);
            max_z_solved = true;
        }
    }
}


template <typename realtype>
void
YoungLaplaceShape<realtype>::step_DBo()
{
    int flag;
    detail::sunreal tcur, tnext;

    flag = ERKStepGetCurrentTime(arkode_mem_DBo, &tcur);
    if (flag == ARK_MEM_NULL) throw std::runtime_error("ARK_MEM_NULL");

    if (tcur == RCONST(0.0)) {
        // First step. Set tout to 0.1 to give a rough scale of t variable when using ARK_ONE_STEP.
        tnext = tcur + RCONST(0.1);
    } else {
        tnext = INFINITY;
    }

    flag = ERKStepEvolve(arkode_mem_DBo, tnext, nv_DBo, &tcur, ARK_ONE_STEP);
    if (flag < 0) throw std::runtime_error("ERKStepEvolve() failed.");

    realtype y[2], dy_ds[2], d2y_ds2[2];
    y[0] = NV_Ith_S(nv_DBo, 0);
    y[1] = NV_Ith_S(nv_DBo, 1);
    dy_ds[0] = NV_Ith_S(nv_DBo, 2);
    dy_ds[1] = NV_Ith_S(nv_DBo, 3);

    ode_DBo(this, bond, y, dy_ds, d2y_ds2);

    dense_DBo.push_back(tcur, y, dy_ds, d2y_ds2);
}


template <typename realtype>
int
YoungLaplaceShape<realtype>::
arkrhs(detail::sunreal s, const N_Vector nv, N_Vector nvdot, void *user_data)
{
    auto self = static_cast<YoungLaplaceShape<realtype> *>(user_data);

    const detail::sunreal *y = NV_DATA_S(nv);
    const detail::sunreal *dy_ds = y + 2;

    detail::sunreal *out_dy_ds = NV_DATA_S(nvdot);
    detail::sunreal *out_d2y_ds2 = out_dy_ds + 2;

    out_dy_ds[0] = dy_ds[0];
    out_dy_ds[1] = dy_ds[1];

    ode(self, s, y, dy_ds, out_d2y_ds2);

    // Return with success.
    return 0;
}


template <typename realtype>
int
YoungLaplaceShape<realtype>::
arkrhs_DBo(detail::sunreal s, const N_Vector nv, N_Vector nvdot, void *user_data) {
    auto self = static_cast<YoungLaplaceShape<realtype> *>(user_data);

    const detail::sunreal *y = NV_DATA_S(nv);
    const detail::sunreal *dy_ds = y + 2;

    detail::sunreal *out_dy_ds = NV_DATA_S(nvdot);
    detail::sunreal *out_d2y_ds2 = out_dy_ds + 2;

    out_dy_ds[0] = dy_ds[0];
    out_dy_ds[1] = dy_ds[1];

    ode_DBo(self, s, y, dy_ds, out_d2y_ds2);

    // Return with success.
    return 0;
}


template <typename realtype>
int
YoungLaplaceShape<realtype>::
arkrhs_vol(detail::sunreal s, const N_Vector nv, N_Vector nvdot, void *user_data) {
    auto self = static_cast<YoungLaplaceShape<realtype> *>(user_data);

    ode_vol(self, s, NV_DATA_S(nv), NV_DATA_S(nvdot));

    // Return with success.
    return 0;
}


template <typename realtype>
int
YoungLaplaceShape<realtype>::
arkrhs_surf(detail::sunreal s, const N_Vector nv, N_Vector nvdot, void *user_data) {
    auto self = static_cast<YoungLaplaceShape<realtype> *>(user_data);

    ode_surf(self, s, NV_DATA_S(nv), NV_DATA_S(nvdot));

    // Return with success.
    return 0;
}


template <typename realtype>
int
YoungLaplaceShape<realtype>::
arkroot(detail::sunreal s, const N_Vector nv, detail::sunreal *out, void *user_data)
{
    const detail::sunreal *y = NV_DATA_S(nv);
    const detail::sunreal *dy_ds = y + 2;

    // Set root to be dz_ds = 0.
    out[0] = dy_ds[1];

    // Return with success.
    return 0;
}


template <typename realtype>
template <typename T, typename RandomAccessIt1, typename RandomAccessIt2, typename OutputIt>
void
YoungLaplaceShape<realtype>::
ode(YoungLaplaceShape<realtype> *self,
    const T &s,
    const RandomAccessIt1 y,
    const RandomAccessIt2 dy_ds,
    OutputIt d2y_ds2)
{
    static const realtype INFITESIMAL = std::numeric_limits<realtype>::denorm_min();

    auto const &r = y[0];
    auto const &z = y[1];
    auto const &dr_ds = dy_ds[0];
    auto const &dz_ds = dy_ds[1];

    auto dphi_ds = 2.0 - (self->bond)*z - (dz_ds + INFITESIMAL)/(r + INFITESIMAL);

    *d2y_ds2++ = -dz_ds * dphi_ds;
    *d2y_ds2++ =  dr_ds * dphi_ds;
}


template <typename realtype>
template <typename T, typename RandomAccessIt1, typename RandomAccessIt2, typename OutputIt>
void
YoungLaplaceShape<realtype>::
ode_DBo(YoungLaplaceShape<realtype> *self,
        const T &s,
        const RandomAccessIt1 y,
        const RandomAccessIt2 dy_ds,
        OutputIt d2y_ds2)
{
    using namespace boost::math::differentiation;

    static const realtype INFITESIMAL = std::numeric_limits<realtype>::denorm_min();

    auto const &dr_dBo = y[0];
    auto const &dz_dBo = y[1];
    auto const &d2r_dBods = dy_ds[0];
    auto const &d2z_dBods = dy_ds[1];

    auto const f = (*self)(make_fvar<realtype, 1>(s));
    realtype r = f[0].derivative(0);
    realtype z = f[1].derivative(0);
    realtype dr_ds = f[0].derivative(1);
    realtype dz_ds = f[1].derivative(1);

    auto dphi_ds = 2.0 - (self->bond)*z - (dz_ds + INFITESIMAL)/(r + INFITESIMAL);
    auto d2phi_dBods = -z - dz_dBo*(self->bond) - d2z_dBods/(r + INFITESIMAL) + dr_dBo*dz_ds/(r*r + INFITESIMAL);

    *d2y_ds2++ = -d2z_dBods * dphi_ds - dz_ds * d2phi_dBods;
    *d2y_ds2++ =  d2r_dBods * dphi_ds + dr_ds * d2phi_dBods;
}


template <typename realtype>
template <typename T, typename RandomAccessIt, typename OutputIt>
void
YoungLaplaceShape<realtype>::
ode_vol(YoungLaplaceShape<realtype> *self,
        const T &s,
        const RandomAccessIt y,
        OutputIt dy_ds)
{
    using namespace boost::math::differentiation;

    auto const f = (*self)(make_fvar<realtype, 1>(s));
    realtype r = f[0].derivative(0);
    realtype dz_ds = f[1].derivative(1);

    *dy_ds = boost::math::constants::pi<realtype>() * r*r * dz_ds;
}


template <typename realtype>
template <typename T, typename RandomAccessIt, typename OutputIt>
void
YoungLaplaceShape<realtype>::
ode_surf(YoungLaplaceShape<realtype> *self,
        const T &s,
        const RandomAccessIt y,
        OutputIt dy_ds)
{
    using namespace boost::math::differentiation;

    realtype r = (*self)(s)[0];

    *dy_ds = 2 * boost::math::constants::pi<realtype>() * r;
}


}  // namespace younglaplace
}  // namespace opendrop

#endif
