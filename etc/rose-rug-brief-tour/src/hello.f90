program hello
implicit none
character(*), parameter :: greeter_env = 'HELLO_GREETER', target_env = 'WORLD'
character(31) :: greeter, target_override
character(*), parameter :: jup_lang_env = 'LANG_JUPITER'
character(31) :: jup_language
character(*), parameter :: jupiter_target = 'JUPITER'
character(*), parameter :: max_targets_env = 'MAX_TARGETS'
character(31) :: max_targets_value
integer :: i, i_arg, code, max_targets, num_targets
character(1024) :: file_name
character(31) :: salutation = 'hello', targets(31) = 'world'
character(*), parameter :: hello_targets_nl_file = 'hello-targets.nl'
namelist /targets_nl/ targets
call get_environment_variable(greeter_env, value=greeter, status=code)
if (code /= 0) then
    call get_environment_variable('LOGNAME', value=greeter, status=code)
end if
if (code /= 0) then
    write(0, '(a)') '[FAIL] ' // greeter_env // ' and LOGNAME not defined'
    stop 1
end if
open(1, file=hello_targets_nl_file, action='read', status='old', iostat=code)
if (code == 0) then
    read(1, nml=targets_nl)
    close(1)
end if
call get_environment_variable(target_env, value=target_override, status=code)
if (code == 0) then
    do i = 1, size(targets)
        targets(i) = target_override
    end do
    if (target_override == jupiter_target) then
        call get_environment_variable(jup_lang_env, value=jup_language, &
        & status=code)
        if (jup_language == "Europan") then
            salutation = "Ice to see you"
        end if
    end if
end if
num_targets = size(targets)
call get_environment_variable(max_targets_env, value=max_targets_value, status=code)
if (code == 0) then
    read(max_targets_value, *), max_targets
    if (num_targets < max_targets) then
        num_targets = max_targets
    end if
end if
do i_arg = 1, command_argument_count()
    call get_command_argument(i_arg, file_name, status=code)
    if (code == 0) then
        open(10, file=file_name, action='write')
        do i = 1, num_targets
            write(10, '(a,a,1x,a)') trim(greeter), ': ' // salutation, trim(targets(i))
        end do
        close(10)
    end if
end do
do i = 1, num_targets
    write(*, '(a,a,1x,a)') trim(greeter), ': ' // salutation, trim(targets(i))
end do
write(0, '(a,1x,a,a,1x,i0,1x,a)') &
    '[DIAG]', trim(greeter), ': greeted', size(targets), 'people.'
end program hello
