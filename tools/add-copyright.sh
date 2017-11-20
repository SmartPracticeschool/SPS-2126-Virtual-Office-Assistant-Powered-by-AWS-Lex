for f in */*.py; do
   if grep -v -q "# Copyright [0-9]{4} Amazon.com" $f; then
       echo $f
       cat ./copyright.py $f > $f.new
       mv $f.new $f
   fi
done
