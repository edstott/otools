folder = 'd:\estott\Stuff\omaps\maryon\DTM';
tilesize = 1000;
contourint = 2.5;

%Get filenames
files = ls([folder,'\*.asc*']);

%Work out tile arrangement
east = files(:,3)*20+files(:,4)*2+(files(:,8)=='e');
east = east - min(east);
north = files(:,5)*20+files(:,6)*2+(files(:,7)=='n');
north = north - min(north);

%Set up height matrix
hdata = zeros((max(north)+1)*tilesize,(max(east)+1)*tilesize);

%Read each file into correcto portion of height matrix
for i=1:size(files,1)
    disp(['Loading file ',files(i,:)]);
    fdata = importdata([folder,'\',files(i,:)],' ',6);
    hdata(north(i)*1000+1:north(i)*1000+1000,east(i)*1000+1:east(i)*1000+1000) = flipud(fdata.data);
end

%Determine contour intervals
minelev = min(min(hdata));
maxelev = max(max(hdata));
contourelev = ceil(minelev/contourint)*contourint:contourint:maxelev;

figure;
hold on;
imshow(hdata,[minelev,maxelev]);
contours = contour(hdata,contourelev);

