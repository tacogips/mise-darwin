function bkms
    set -l home_dir $HOME
    set -l bookmark_dir $home_dir/.private/bookmarks
    if test -d $bookmark_dir
        for file in $bookmark_dir/*
            if test -f $file
                set -l filename (path basename --no-extension $file)
                set -l content (cat $file)
                echo "bookmark_$filename $content"

            end
        end
    else
        echo "Error: Bookmark directory $bookmark_dir does not exist"
        return 1
    end
end
