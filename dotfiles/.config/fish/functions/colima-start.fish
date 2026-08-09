function colima-start --description 'Start Colima with 4 CPUs and 8 GiB by default'
    set -l extra_args
    if not contains -- --cpu $argv; and not string match -q -- '--cpu=*' $argv
        set -a extra_args --cpu 4
    end
    if not contains -- --memory $argv; and not string match -q -- '--memory=*' $argv
        set -a extra_args --memory 8
    end
    colima start $extra_args $argv
end
