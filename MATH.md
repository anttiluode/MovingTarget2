# A remembered object as a family of responses

Antti's question was whether an object can keep answering new pings while the neural coordinates carrying it change. This note gives one exact, bounded instance of that idea. It also shows why predicting the next answer is weaker than having a complete state for every future interaction.

## 1. State, query, and observable

Group g contains U unit-radius oscillators,

$$z_{gu}=e^{i\theta_{gu}}.$$

A query point q determines a pulse phase through a fixed, known wavevector:

$$\phi_g(q)=k_g^{\mathsf T}q.$$

The pulse adds a complex vector and the unit relaxes back to unit radius:

$$z_{gu}\longmapsto \frac{z_{gu}+a e^{i\phi_g(q)}}{|z_{gu}+a e^{i\phi_g(q)}|}.$$

For real a with |a|<1, the phase advance is exactly

$$\delta_{gu}(q;a)=\operatorname{Im}\log\left(1+a e^{i\phi_g(q)}e^{-i\theta_{gu}}\right).$$

The disk centered at 1 with radius |a| stays in the right half-plane, so this principal logarithm has no branch ambiguity. The software observable is

$$R_\theta(q;a)=\frac{1}{GU}\sum_{g,u}\delta_{gu}(q;a).$$

It is an average of measured phase changes. A voltage sum on a wire is a different observable; this experiment does not implement that interface.

## 2. The response code is a hierarchy of moments

Define the complex phase moments

$$m_{g\ell}=\frac{1}{U}\sum_u e^{-i\ell\theta_{gu}}.$$

The standard logarithmic power series gives the exact answer

$$R_\theta(q;a)=\frac{1}{G}\sum_g\sum_{\ell=1}^{\infty}\frac{(-1)^{\ell+1}a^\ell}{\ell}\operatorname{Im}\left(e^{i\ell\phi_g(q)}m_{g\ell}\right).$$

Thus an order-L code stores G complex moments at each of L orders: 2GL real scalars. It generates answers to continuous new q, rather than storing a table of old answers.

Since |m_gl|<=1, truncation has the uniform bound

$$|R_\theta(q;a)-R^{(L)}_\theta(q;a)|\leq\sum_{\ell=L+1}^{\infty}\frac{|a|^\ell}{\ell}\leq\frac{|a|^{L+1}}{(L+1)(1-|a|)}.$$

This is an absolute error bound, not a bound on the reported NRMSE; the latter also depends on the size of the reference responses.

## 3. Weak pings see a small behavioral state

To first order,

$$R_\theta(q;a)=\frac{a}{G}\sum_g\operatorname{Im}\left(e^{i\phi_g(q)}m_{g1}\right)+O(a^2).$$

For the six known wavevectors in the protocol, this is a twelve-dimensional real response family. Each moment supplies a sine coefficient and a cosine coefficient. The modes are distinct on the query torus, so those twelve coefficients can be identified from a full-rank set of calibration queries.

Let c stack their real and imaginary parts. Then

$$R^{(1)}_\theta(q;a)=b(q,a)^{\mathsf T}c.$$

Here the state determines c and the ping determines b. This is the precise summing-and-multiplying object from Antti's image. The finite-strength response uses a hierarchy of higher moments; it is not globally described by that one first-order vector.

## 4. Changing coordinates while keeping the weak object

The map from a group's U angles to its first moment is

$$C_g(\theta_g)=\begin{pmatrix}U^{-1}\sum_u\cos\theta_{gu}\\U^{-1}\sum_u\sin\theta_{gu}\end{pmatrix}.$$

At a regular point its derivative has rank two. A fixed-moment level surface therefore has U-2 local dimensions. Six groups of sixteen units leave **84 local directions of internal change** while their twelve first-order response coordinates stay fixed.

The drift generator projects a random velocity v onto the tangent space of this level surface:

$$v_\perp=\left[I-J^{\mathsf T}(JJ^{\mathsf T})^\dagger J\right]v,\qquad J=DC_g.$$

Finite steps require a numerical retraction onto the constraint surface. Every call uses the moment of its current input state. It does not carry an old reference that would repair read damage.

A fully coherent group has |m_g1|=1 and no internal phase freedom at fixed moment; the implementation leaves it stationary. This is a boundary case, not a failure to generate drift.

First-moment preservation is imposed by the simulator. The result is a controlled test of what such preservation buys. The experiment does not explain how a biological population would enforce it.

## 5. Equivalence depends on the strength of interrogation

If two states have identical first moments, all their first-order query responses agree. For finite a their exact answers need not agree. The uniform difference bound is

$$|R_\theta(q;a)-R_{\tilde\theta}(q;a)|\leq\frac{|a|^2}{1-|a|}.$$

The bound follows by applying the order-1 remainder bound to both states. It is deliberately conservative.

A hand-checkable single-group counterexample is

$$\theta_A=(\pi/3,-\pi/3,\pi/3,-\pi/3),\qquad\theta_B=(0,0,0,\pi).$$

Both have m1=1/2, but m2=-1/2 for A and m2=1 for B. They agree to first order and diverge under stronger pings. This is covered by an analytic test independent of the full experiment.

The statement “this is the same object” therefore needs a query family and an error tolerance. Under weak pings, the first-moment code is an approximate behavioral equivalence. Stronger pings resolve differences it discards.

## 6. A sufficient answer code need not be a sufficient dynamical state

A weak read changes each phase by

$$\theta'_{gu}=\theta_{gu}+a\sin(\phi_g-\theta_{gu})+O(a^2).$$

Consequently the first moment after the read is

$$m'_{g1}=m_{g1}+\frac{a}{2}\left(e^{-i\phi_g}-e^{i\phi_g}m_{g2}\right)+O(a^2).$$

**The first-order update of the first moment depends on the second moment.** Two populations can have the same weak-answer code yet evolve into different codes after the same read. Thus twelve numbers do not close the full read-and-update dynamics, even though they predict present weak answers well.

This connects directly to VMNClaude's compressed-answer undo failure: compression can discard details that matter when the system changes. It also explains why “more coefficients can reconstruct today's answer” is different from “the old memory was preserved.”

## 7. Compensation lowers the disturbance order

Let alpha=phi-theta. A pulse followed by radial relaxation, then the same pulse with reversed sign, leaves

$$\theta''-\theta=-\frac{a^2}{2}\sin(2\alpha)+O(a^3).$$

The leading O(a) phase kick cancels without needing to read the individual state. The O(a^2) remainder generally persists and can accumulate. In this simplified experiment, cancellation assumes unit radii, identical pulse phases, and instantaneous radial normalization between pulses.

These assumptions are stronger than VMN's noisy finite-time dynamics. The measured compensation ratio here is not a hardware performance prediction or a replacement for VMN's earlier result.

## 8. Coordinates, tensor language, and meaning

For a genuinely linear state coordinate change x'=Sx, a grounded linear reader w must transform as w'=S^{-\mathsf T}w to preserve w^T x. If the reader or the query port does not transform appropriately, a coordinate change need not preserve behavior. This is standard covariant/contravariant bookkeeping.

Our first-moment reduction is more than renaming coordinates: many different physical angle configurations map to the same small response code. The relevant object is that many-to-one behavioral map and the query resolution at which it is adequate. Tensor language can describe the multilinear terms; it does not automatically prove stability, compactness, or semantic identity.

MovingProblem showed another boundary: an oriented statistical frame can acquire a sign reversal around a closed loop even with a healthy local eigengap. MovingTarget2 avoids that tracking problem by assuming fixed semantic group-to-query assignments. The cross-group shuffle control exposes the cost of that assumption.
