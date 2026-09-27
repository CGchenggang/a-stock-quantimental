from astock_v2.validation import walk_forward_windows

def test_walk_forward_windows_are_time_ordered_and_non_overlapping():
    windows=walk_forward_windows(list(range(10)),train_size=4,test_size=2)
    assert len(windows)==3
    assert windows[0].train==(0,1,2,3)
    assert windows[0].test==(4,5)
    assert windows[1].train==(2,3,4,5)
    assert windows[1].test==(6,7)

def test_walk_forward_can_use_explicit_step():
    windows=walk_forward_windows(list(range(8)),train_size=3,test_size=2,step=1)
    assert windows[-1].test==(6,7)

def test_walk_forward_gap_embargoes_test_start():
    windows=walk_forward_windows(list(range(10)),train_size=4,test_size=2,gap=1)
    assert windows[0].train==(0,1,2,3)
    assert windows[0].test==(5,6)
    assert windows[0].train_end==4
    assert windows[0].test_start==5
