BEGIN {
    cnt = 0
    last = ""
}
{
    if ($0 != last)
    {
        if(last != "")
        {
            if(cnt >= MIN)
            {
                print cnt " = " last
            }
        }
        cnt = 0
    }
    cnt++
    last = $0
}
END {
    if(cnt >= MIN)
    {
        print cnt " = " last
    }
}

