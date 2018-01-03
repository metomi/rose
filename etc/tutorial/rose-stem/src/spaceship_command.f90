PROGRAM spaceship_command

IMPLICIT NONE

INTEGER, PARAMETER :: tmax = 10 ! Number of timesteps

REAL :: position(3) = 0.0
REAL :: velocity(3) = 0.0
REAL :: acceleration(3) = 0.0
REAL :: thrust(3, tmax) = 0.0
REAL :: mass = 1.0

! Timestep
REAL, PARAMETER :: dt = 1.0

INTEGER :: i, j

NAMELIST /spaceship/ position, mass
NAMELIST /command/ thrust

OPEN(UNIT=1, FILE='spaceship.NL', ACTION='read', STATUS='old')
READ(1, NML=spaceship)
CLOSE(UNIT=1)

OPEN(UNIT=2, FILE='command.NL', ACTION='read', STATUS='old')
READ(2, NML=command)
CLOSE(UNIT=2)

OPEN(UNIT=3, FILE='output.txt')
WRITE(3, '(A)') 'Time: t=0.0'
WRITE(3, '(A,3(F7.3,A))') 'Position: ',position(1),',',position(2),',',position(3)
WRITE(3, '(A,3(F7.3,A))') 'Velocity: ',velocity(1),',',velocity(2),',',velocity(3)
WRITE(3, '(/)')

DO i = 1, tmax
  acceleration = thrust(:, i) / mass
  velocity = velocity + acceleration * dt
  position = position + velocity * dt
  WRITE(3, '(A, F7.3)') 'Time: t=',dt * i
  WRITE(3, '(A,3(F7.3,A))') 'Acceleration:',acceleration(1),',',acceleration(2),',',acceleration(3)
  WRITE(3, '(A,3(F7.3,A))') 'Position: ',position(1),',',position(2),',',position(3)
  WRITE(3, '(A,3(F7.3,A))') 'Velocity: ',velocity(1),',',velocity(2),',',velocity(3)
  WRITE(3, '(/)')
END DO

CLOSE(UNIT=3)

END PROGRAM spaceship_command
